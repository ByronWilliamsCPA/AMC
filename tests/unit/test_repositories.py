"""Unit tests for repository methods not fully exercised by the API tests.

Targets invite expiry/redemption, session sliding and revocation, the user
count bootstrap helper, and attempt-history ordering, against the in-memory
database fixture.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

import pytest

from amc.core.security import generate_invite_token, hash_password
from amc.models.base import utcnow
from amc.repositories.attempts import (
    TestAttemptRepository as ExamAttemptRepository,
)
from amc.repositories.catalog import ExamRepository
from amc.repositories.users import (
    InviteRepository,
    SessionRepository,
    UserRepository,
)
from amc.services.grading import score_exam

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.unit


async def _make_user(db: AsyncSession, email: str = "u@example.com") -> object:
    return await UserRepository(db).create(
        email=email,
        display_name="U",
        role="student",
        password_hash=hash_password("password-123"),
    )


class TestUserRepository:
    async def test_count_and_get_by_email_case_insensitive(
        self, db_session: AsyncSession
    ) -> None:
        users = UserRepository(db_session)
        assert await users.count() == 0
        await _make_user(db_session, "Mixed@Example.com")
        assert await users.count() == 1
        # Stored and looked up lower-cased.
        assert await users.get_by_email("mixed@example.com") is not None
        assert await users.get_by_email("MIXED@EXAMPLE.COM") is not None


class TestInviteRepository:
    async def test_valid_then_redeemed_is_invalid(
        self, db_session: AsyncSession
    ) -> None:
        creator = await _make_user(db_session, "creator@example.com")
        invites = InviteRepository(db_session)
        token = generate_invite_token()
        invite = await invites.create(
            raw_token=token,
            email="invitee@example.com",
            role="student",
            created_by=creator.id,  # type: ignore[attr-defined]
            ttl_seconds=3600,
        )
        assert await invites.get_valid_by_token(token) is not None
        await invites.mark_redeemed(invite)
        assert await invites.get_valid_by_token(token) is None

    async def test_expired_invite_is_invalid(self, db_session: AsyncSession) -> None:
        creator = await _make_user(db_session, "creator2@example.com")
        invites = InviteRepository(db_session)
        token = generate_invite_token()
        invite = await invites.create(
            raw_token=token,
            email="late@example.com",
            role="student",
            created_by=creator.id,  # type: ignore[attr-defined]
            ttl_seconds=3600,
        )
        invite.expires_at = utcnow() - timedelta(minutes=1)
        await db_session.flush()
        assert await invites.get_valid_by_token(token) is None

    async def test_unknown_token_is_none(self, db_session: AsyncSession) -> None:
        assert await InviteRepository(db_session).get_valid_by_token("nope") is None


class TestSessionRepository:
    async def test_create_get_slide_revoke(self, db_session: AsyncSession) -> None:
        user = await _make_user(db_session, "sess@example.com")
        sessions = SessionRepository(db_session)
        record = await sessions.create(user_id=user.id, ttl_seconds=3600)  # type: ignore[attr-defined]

        active = await sessions.get_active(record.id)
        assert active is not None

        original = active.expires_at
        await sessions.slide_expiry(active, ttl_seconds=7200)
        assert active.expires_at > original

        await sessions.revoke(active)
        assert await sessions.get_active(record.id) is None

    async def test_expired_session_inactive(self, db_session: AsyncSession) -> None:
        user = await _make_user(db_session, "exp@example.com")
        sessions = SessionRepository(db_session)
        record = await sessions.create(user_id=user.id, ttl_seconds=3600)  # type: ignore[attr-defined]
        record.expires_at = utcnow() - timedelta(seconds=1)
        await db_session.flush()
        assert await sessions.get_active(record.id) is None


class TestExamRepository:
    async def test_get_missing_returns_none(self, db_session: AsyncSession) -> None:
        import uuid

        assert await ExamRepository(db_session).get_with_problems(uuid.uuid4()) is None


class TestExamAttemptRepository:
    async def test_record_and_list(self, db_session: AsyncSession) -> None:
        from amc.models import Exam

        user = await _make_user(db_session, "att@example.com")
        exam = Exam(
            contest="AMC 8",
            year=2017,
            variant="",
            duration_sec=2400,
            score_mode="count",
            num_problems=2,
            voided=[],
        )
        db_session.add(exam)
        await db_session.flush()

        score = score_exam(
            answer_key=["A", "B"], answers=["A", "B"], score_mode="count"
        )
        repo = ExamAttemptRepository(db_session)
        await repo.record(
            user_id=user.id,  # type: ignore[attr-defined]
            exam_id=exam.id,
            answers=["A", "B"],
            flags=[False, False],
            time_used_sec=30,
            score=score,
        )
        history = await repo.list_for_user(user.id)  # type: ignore[attr-defined]
        assert len(history) == 1
        assert history[0].score == 2.0
