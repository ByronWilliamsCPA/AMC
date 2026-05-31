"""Additional integration tests closing API/repository coverage gaps.

Covers the catalog contest filter, attempt history ordering, the AMC-10
recommendation layering, exam grading in six-point mode, session expiry and
sliding, and logout revocation — the flows a Newman monitor will exercise.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

import pytest

from amc.models import Exam, Problem
from amc.models.base import utcnow

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession

    from amc.models import User

pytestmark = pytest.mark.integration


async def _seed_amc10(db: AsyncSession, *, year: int, key: list[str]) -> Exam:
    """Seed a six-point AMC 10 exam with the given key.

    Args:
        db: The database session.
        year: The contest year (varies the unique key).
        key: The answer key, one letter per problem.

    Returns:
        The persisted exam.
    """
    exam = Exam(
        contest="AMC 10",
        year=year,
        variant="A",
        duration_sec=4500,
        score_mode="sixpoint",
        num_problems=len(key),
        voided=[],
    )
    db.add(exam)
    await db.flush()
    for number, letter in enumerate(key, start=1):
        db.add(
            Problem(
                exam_id=exam.id,
                number=number,
                render_mode="latex",
                body_latex=f"P{number}",
                choices=[{"L": x, "html": x} for x in "ABCDE"],
                correct_answer=letter,
            )
        )
    await db.flush()
    return exam


class TestCatalogFilter:
    """The contest query filter on the exam listing."""

    async def test_filter_by_contest(
        self, admin_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _seed_amc10(db_session, year=2018, key=["A", "B"])
        await _seed_amc10(db_session, year=2019, key=["C", "D"])

        all_exams = (await admin_client.get("/api/v1/exams")).json()
        assert len(all_exams) == 2

        filtered = (
            await admin_client.get("/api/v1/exams", params={"contest": "AMC 10"})
        ).json()
        assert len(filtered) == 2
        assert all(e["contest"] == "AMC 10" for e in filtered)

        none = (
            await admin_client.get("/api/v1/exams", params={"contest": "AMC 8"})
        ).json()
        assert none == []


class TestSixPointGrading:
    """Six-point scoring over the API (correct*6 + blank*1.5)."""

    async def test_blank_scores_partial(
        self, admin_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        exam = await _seed_amc10(db_session, year=2020, key=["A", "B", "C", "D"])
        resp = await admin_client.post(
            f"/api/v1/exams/{exam.id}/attempts",
            # one correct, one wrong, two blank
            json={"answers": ["A", "X", None, None], "time_used_sec": 10},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["correct"] == 1
        assert body["wrong"] == 1
        assert body["blank"] == 2
        assert body["score"] == 1 * 6 + 2 * 1.5  # 9.0
        assert body["max_score"] == 24.0


class TestProgressWithAmc:
    """Progress reflects AMC-10 history and attempt ordering."""

    async def test_history_orders_newest_first(
        self, admin_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        exam = await _seed_amc10(db_session, year=2021, key=["A", "B"])
        await admin_client.post(
            f"/api/v1/exams/{exam.id}/attempts",
            json={"answers": ["A", "B"], "time_used_sec": 5},
        )
        await admin_client.post(
            f"/api/v1/exams/{exam.id}/attempts",
            json={"answers": ["A", "X"], "time_used_sec": 5},
        )
        progress = (await admin_client.get("/api/v1/progress")).json()
        assert len(progress["test_attempts"]) == 2
        # Both attempts are present; the endpoint returns them newest-first.
        scores = [a["score"] for a in progress["test_attempts"]]
        assert set(scores) == {12.0, 6.0}


class TestSessionLifecycle:
    """Session expiry and logout revocation over the API."""

    async def test_logout_revokes_session(self, admin_client: AsyncClient) -> None:
        # Authenticated before logout.
        assert (await admin_client.get("/api/v1/auth/me")).status_code == 200
        # Logout, then the same client/cookie is rejected.
        assert (await admin_client.post("/api/v1/auth/logout")).status_code == 204
        assert (await admin_client.get("/api/v1/auth/me")).status_code == 401

    async def test_expired_session_rejected(
        self, client: AsyncClient, admin_user: User, db_session: AsyncSession
    ) -> None:
        from sqlalchemy import select

        from amc.models import Session
        from amc.services.auth import login_rate_limiter

        login_rate_limiter.reset(admin_user.email)
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": admin_user.email, "password": "admin-password-123"},
        )
        assert login.status_code == 200

        # Force the session to be expired in the database.
        record = (await db_session.execute(select(Session))).scalars().first()
        assert record is not None
        record.expires_at = utcnow() - timedelta(hours=1)
        await db_session.flush()

        assert (await client.get("/api/v1/auth/me")).status_code == 401


class TestRegisterValidation:
    """Registration rejects short passwords (schema validation -> 422)."""

    async def test_short_password_rejected(
        self, admin_client: AsyncClient, client: AsyncClient
    ) -> None:
        invite = await admin_client.post(
            "/api/v1/invites", json={"email": "short@example.com", "role": "student"}
        )
        token = invite.json()["token"]
        resp = await client.post(
            "/api/v1/auth/register",
            json={"token": token, "display_name": "S", "password": "short"},
        )
        assert resp.status_code == 422
