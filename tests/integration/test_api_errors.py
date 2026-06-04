"""Integration tests for API error paths and edge cases.

Covers not-found mapping (404), invalid-invite handling, logout idempotency,
the /auth/me endpoint, and invalid-role rejection so the exception-to-HTTP
mapping and router guards are exercised.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient

    from amc.models import User

pytestmark = pytest.mark.integration


class TestNotFound:
    """Missing resources map to 404 via the exception handler."""

    async def test_missing_exam(self, admin_client: AsyncClient) -> None:
        resp = await admin_client.get(f"/api/v1/exams/{uuid.uuid4()}")
        assert resp.status_code == 404
        assert resp.json()["error"] == "ResourceNotFoundError"

    async def test_missing_diagnostic(self, admin_client: AsyncClient) -> None:
        resp = await admin_client.get("/api/v1/diagnostics/does-not-exist")
        assert resp.status_code == 404

    async def test_submit_missing_exam(self, admin_client: AsyncClient) -> None:
        resp = await admin_client.post(
            f"/api/v1/exams/{uuid.uuid4()}/attempts",
            json={"answers": ["A"], "time_used_sec": 1},
        )
        assert resp.status_code == 404

    async def test_progress_for_missing_user(self, admin_client: AsyncClient) -> None:
        resp = await admin_client.get(f"/api/v1/users/{uuid.uuid4()}/progress")
        assert resp.status_code == 404


class TestInviteValidation:
    """Invite validation and redemption edge cases."""

    async def test_unknown_token_is_invalid(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/auth/invites/not-a-real-token")
        assert resp.status_code == 200
        assert resp.json() == {"valid": False, "email": None, "role": None}

    async def test_register_with_bad_token(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "token": "bogus",
                "display_name": "X",
                "password": "password-123",
            },
        )
        assert resp.status_code == 400

    async def test_invalid_role_rejected(self, admin_client: AsyncClient) -> None:
        resp = await admin_client.post(
            "/api/v1/invites",
            json={"email": "x@example.com", "role": "superuser"},
        )
        assert resp.status_code == 400


class TestSessionEndpoints:
    """me and logout behaviour."""

    async def test_me_returns_current_user(
        self, admin_client: AsyncClient, admin_user: User
    ) -> None:
        resp = await admin_client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        assert resp.json()["email"] == admin_user.email

    async def test_logout_is_idempotent(self, client: AsyncClient) -> None:
        # Logout without a session still succeeds (clears cookie, 204).
        resp = await client.post("/api/v1/auth/logout")
        assert resp.status_code == 204

    async def test_login_wrong_password(
        self, client: AsyncClient, admin_user: User
    ) -> None:
        from amc.services.auth import login_rate_limiter

        login_rate_limiter.reset(admin_user.email)
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": admin_user.email, "password": "nope"},
        )
        assert resp.status_code == 401
        # Generic message: must not reveal that the email exists.
        assert "Invalid email or password" in resp.text
        login_rate_limiter.reset(admin_user.email)

    async def test_login_unknown_email(self, client: AsyncClient) -> None:
        from amc.services.auth import login_rate_limiter

        login_rate_limiter.reset("ghost@example.com")
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@example.com", "password": "whatever"},
        )
        assert resp.status_code == 401
        # Same status and message as a wrong password for a real account, so the
        # response content does not reveal whether the email is registered
        # (the timing parity is handled by the dummy-hash verify in the route).
        assert "Invalid email or password" in resp.text

    async def test_login_unknown_email_runs_dummy_verify(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The timing half of the user-enumeration mitigation depends on running
        # the Argon2 verify even when the email is unknown. The response-content
        # assertions above stay green even if that verify were removed, so spy on
        # the route's verify_password to lock the behaviour in: a regression that
        # short-circuits the unknown-email path would reopen the timing oracle.
        from amc.api import auth as auth_module
        from amc.services.auth import login_rate_limiter

        hashes_verified: list[str] = []
        real_verify = auth_module.verify_password

        def _spy(password: str, password_hash: str) -> bool:
            hashes_verified.append(password_hash)
            return real_verify(password, password_hash)

        monkeypatch.setattr(auth_module, "verify_password", _spy)

        login_rate_limiter.reset("ghost-timing@example.com")
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "ghost-timing@example.com", "password": "whatever"},
        )
        assert resp.status_code == 401
        # The unknown-email path must verify against the module dummy hash, so it
        # pays the same Argon2 cost as a known account (constant-work timing).
        assert hashes_verified == [auth_module._DUMMY_PASSWORD_HASH]
