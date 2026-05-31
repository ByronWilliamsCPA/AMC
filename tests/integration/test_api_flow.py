"""End-to-end API tests over the in-memory database.

Exercises the security boundary (no answer keys pre-submission), the full
invite -> register -> login -> exam-submit -> progress flow, RBAC on the
cross-user progress endpoint, and login rate limiting.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient

    from amc.models import DiagnosticInstrument, Exam, User

pytestmark = pytest.mark.integration


class TestHealth:
    """The health endpoint is unauthenticated and green."""

    async def test_liveness(self, client: AsyncClient) -> None:
        resp = await client.get("/health/live")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestAuthRequired:
    """Catalog and progress require authentication."""

    async def test_exams_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/exams")
        assert resp.status_code == 401

    async def test_progress_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/progress")
        assert resp.status_code == 401


class TestKeyNeverLeaks:
    """Answer keys must not appear in any pre-submission response."""

    async def test_exam_detail_has_no_answer_key(
        self, admin_client: AsyncClient, seeded_exam: Exam
    ) -> None:
        resp = await admin_client.get(f"/api/v1/exams/{seeded_exam.id}")
        assert resp.status_code == 200
        body = resp.text
        assert "correct_answer" not in body
        # The known keys for the seeded exam must not be exposed as such.
        for problem in resp.json()["problems"]:
            assert "correct_answer" not in problem

    async def test_diagnostic_detail_has_no_answers(
        self, admin_client: AsyncClient, seeded_diagnostic: DiagnosticInstrument
    ) -> None:
        resp = await admin_client.get(f"/api/v1/diagnostics/{seeded_diagnostic.id}")
        assert resp.status_code == 200
        body = resp.json()
        for item in body["items"]:
            assert "answer" not in item
            assert "v" not in item
            assert "accept" not in item


class TestExamSubmission:
    """Submitting an exam grades server-side and persists the attempt."""

    async def test_submit_and_score(
        self, admin_client: AsyncClient, seeded_exam: Exam
    ) -> None:
        # Answer the 3-problem key (A, B, C) with two correct, one wrong.
        resp = await admin_client.post(
            f"/api/v1/exams/{seeded_exam.id}/attempts",
            json={"answers": ["A", "B", "X"], "flags": [], "time_used_sec": 100},
        )
        assert resp.status_code == 200, resp.text
        result = resp.json()
        assert result["correct"] == 2
        assert result["wrong"] == 1
        assert result["score"] == 2.0  # count mode
        # The review reveals the key only now, post-submission.
        assert {item["n"]: item["correct"] for item in result["review"]} == {
            1: "A",
            2: "B",
            3: "C",
        }

    async def test_attempt_appears_in_progress(
        self, admin_client: AsyncClient, seeded_exam: Exam
    ) -> None:
        await admin_client.post(
            f"/api/v1/exams/{seeded_exam.id}/attempts",
            json={"answers": ["A", "B", "C"], "time_used_sec": 60},
        )
        resp = await admin_client.get("/api/v1/progress")
        assert resp.status_code == 200
        progress = resp.json()
        assert len(progress["test_attempts"]) == 1
        assert progress["test_attempts"][0]["score"] == 3.0


class TestDiagnosticSubmission:
    """Diagnostics auto-grade typed answers and trust self-marks."""

    async def test_auto_and_manual_grading(
        self, admin_client: AsyncClient, seeded_diagnostic: DiagnosticInstrument
    ) -> None:
        detail = await admin_client.get(f"/api/v1/diagnostics/{seeded_diagnostic.id}")
        items = {item["label"]: item["id"] for item in detail.json()["items"]}

        resp = await admin_client.post(
            f"/api/v1/diagnostics/{seeded_diagnostic.id}/attempts",
            json={
                "responses": {items["1"]: "4"},
                "marks": {items["2"]: True},
                "elapsed_sec": 30,
            },
        )
        assert resp.status_code == 200, resp.text
        result = resp.json()
        assert result["correct"] == 2
        assert result["total"] == 2
        assert result["passed"] is True


class TestInviteFlow:
    """Invite -> register -> login is the only onboarding path."""

    async def test_full_onboarding(
        self, admin_client: AsyncClient, client: AsyncClient
    ) -> None:
        # Admin mints an invite.
        invite_resp = await admin_client.post(
            "/api/v1/invites",
            json={"email": "student@example.com", "role": "student"},
        )
        assert invite_resp.status_code == 201, invite_resp.text
        token = invite_resp.json()["token"]

        # The token validates publicly.
        check = await client.get(f"/api/v1/auth/invites/{token}")
        assert check.json() == {
            "valid": True,
            "email": "student@example.com",
            "role": "student",
        }

        # The student registers and is logged in.
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "token": token,
                "display_name": "Student",
                "password": "student-pass-123",
            },
        )
        assert reg.status_code == 201, reg.text
        assert reg.json()["email"] == "student@example.com"

        # The same invite cannot be redeemed twice.
        reg2 = await client.post(
            "/api/v1/auth/register",
            json={
                "token": token,
                "display_name": "Imposter",
                "password": "another-pass-123",
            },
        )
        assert reg2.status_code == 400

    async def test_minting_requires_staff(
        self, client: AsyncClient, admin_user: User
    ) -> None:
        # Create and log in as a plain student via an admin-minted invite.
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={"email": admin_user.email, "password": "admin-password-123"},
        )
        assert admin_login.status_code == 200
        invite = await client.post(
            "/api/v1/invites",
            json={"email": "s2@example.com", "role": "student"},
        )
        token = invite.json()["token"]
        await client.post("/api/v1/auth/logout")
        await client.post(
            "/api/v1/auth/register",
            json={
                "token": token,
                "display_name": "S2",
                "password": "s2-password-123",
            },
        )
        # Now authenticated as the student; minting must be forbidden.
        resp = await client.post(
            "/api/v1/invites",
            json={"email": "s3@example.com", "role": "student"},
        )
        assert resp.status_code == 403


class TestRbacProgress:
    """A student cannot read another user's progress; staff can."""

    async def test_student_blocked_from_other_user(
        self, client: AsyncClient, admin_user: User
    ) -> None:
        # Admin mints two student invites and we register both.
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={"email": admin_user.email, "password": "admin-password-123"},
        )
        assert admin_login.status_code == 200
        tokens = []
        for email in ("a@example.com", "b@example.com"):
            inv = await client.post(
                "/api/v1/invites", json={"email": email, "role": "student"}
            )
            tokens.append(inv.json()["token"])
        await client.post("/api/v1/auth/logout")

        # Register student A and capture their id.
        reg_a = await client.post(
            "/api/v1/auth/register",
            json={
                "token": tokens[0],
                "display_name": "A",
                "password": "a-password-123",
            },
        )
        user_a_id = reg_a.json()["id"]
        await client.post("/api/v1/auth/logout")

        # Register student B, then try to read A's progress.
        await client.post(
            "/api/v1/auth/register",
            json={
                "token": tokens[1],
                "display_name": "B",
                "password": "b-password-123",
            },
        )
        resp = await client.get(f"/api/v1/users/{user_a_id}/progress")
        assert resp.status_code == 403

    async def test_staff_can_read_any_user(
        self, admin_client: AsyncClient, client: AsyncClient, admin_user: User
    ) -> None:
        invite = await admin_client.post(
            "/api/v1/invites", json={"email": "c@example.com", "role": "student"}
        )
        token = invite.json()["token"]
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "token": token,
                "display_name": "C",
                "password": "c-password-123",
            },
        )
        user_c_id = reg.json()["id"]
        # admin_client is still the admin session.
        resp = await admin_client.get(f"/api/v1/users/{user_c_id}/progress")
        assert resp.status_code == 200


class TestLoginRateLimit:
    """Repeated failures are throttled (credential-stuffing mitigation)."""

    async def test_lockout_after_repeated_failures(
        self, client: AsyncClient, admin_user: User
    ) -> None:
        from amc.services.auth import login_rate_limiter

        login_rate_limiter.reset(admin_user.email)
        # Exhaust the attempt budget with wrong passwords.
        for _ in range(5):
            bad = await client.post(
                "/api/v1/auth/login",
                json={"email": admin_user.email, "password": "wrong"},
            )
            assert bad.status_code == 401
        # The next attempt is throttled even with the correct password.
        blocked = await client.post(
            "/api/v1/auth/login",
            json={"email": admin_user.email, "password": "admin-password-123"},
        )
        assert blocked.status_code == 401
        assert "Too many attempts" in blocked.json()["message"]
        login_rate_limiter.reset(admin_user.email)
