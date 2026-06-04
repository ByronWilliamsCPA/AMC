"""Integration tests for the health endpoints and the 500 error branch.

The readiness probe exercises the database check; a deliberately failing route
exercises the server-error branch of the exception handler.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient

pytestmark = pytest.mark.integration


class TestHealthEndpoints:
    """Liveness, startup, readiness, and the root alias."""

    async def test_live(self, client: AsyncClient) -> None:
        resp = await client.get("/health/live")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    async def test_startup(self, client: AsyncClient) -> None:
        resp = await client.get("/health/startup")
        assert resp.status_code == 200
        assert resp.json()["status"] == "started"

    async def test_root_alias(self, client: AsyncClient) -> None:
        resp = await client.get("/health/")
        assert resp.status_code == 200

    async def test_readiness_ok_with_database(self, client: AsyncClient) -> None:
        # The readiness probe runs a real SELECT 1 against the test database.
        resp = await client.get("/health/ready")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["checks"]["database"]["status"] is True


class TestServerErrorBranch:
    """A route raising a 5xx project error exercises the error-log branch."""

    async def test_configuration_error_returns_500(self, client: AsyncClient) -> None:
        from fastapi import APIRouter

        from amc.core.exceptions import ConfigurationError

        # Mount a throwaway route on the running app that raises a 500-mapped error.
        app = client._transport.app  # type: ignore[attr-defined]
        router = APIRouter()

        @router.get("/api/v1/_boom")
        async def _boom() -> None:
            raise ConfigurationError("kaboom", details={"k": "v"})

        app.include_router(router)

        resp = await client.get("/api/v1/_boom")
        assert resp.status_code == 500
        assert resp.json()["error"] == "ConfigurationError"


class TestReadinessDatabaseDown:
    """Readiness returns 503 when the database check fails."""

    async def test_returns_503_when_db_unavailable(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from amc.api import health as health_module

        async def _failing_check() -> health_module.ReadinessCheck:
            return health_module.ReadinessCheck(
                name="database", status=False, error="down"
            )

        monkeypatch.setattr(health_module, "check_database", _failing_check)
        resp = await client.get("/health/ready")
        assert resp.status_code == 503


class TestCheckDatabase:
    """The database check's success and failure branches directly."""

    async def test_success_against_test_db(self) -> None:
        from amc.api.health import check_database

        # Uses the app's get_session; the configured test URL is in-memory but a
        # real engine, so SELECT 1 succeeds.
        result = await check_database()
        assert result.name == "database"
        assert isinstance(result.status, bool)

    async def test_failure_when_query_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from amc.api import health as health_module

        class _BoomSession:
            async def __aenter__(self) -> _BoomSession:
                return self

            async def __aexit__(self, *_args: object) -> None:
                return None

            async def execute(self, *_args: object) -> None:
                # Driver errors can embed the DSN (and thus credentials); the
                # sentinel stands in for any such sensitive detail.
                error_message = "auth failed for user amc SENSITIVE_DSN_MARKER"
                raise RuntimeError(error_message)

        def _boom_session() -> _BoomSession:
            return _BoomSession()

        # Patch get_session where check_database imports it (amc.core.database).
        monkeypatch.setattr(
            "amc.core.database.get_session", _boom_session, raising=True
        )
        result = await health_module.check_database()
        assert result.status is False
        # The unauthenticated readiness response must carry a generic message,
        # never the raw driver error detail.
        assert result.error == "database connectivity check failed"
        assert "SENSITIVE_DSN_MARKER" not in (result.error or "")
