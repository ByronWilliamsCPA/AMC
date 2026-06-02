"""Unit tests for the optional OIDC groups-to-roles mapping and route mounting.

The OIDC SSO path is disabled by default; these tests cover the pure role
mapping and that the stub routes are only mounted when explicitly enabled.
"""

from __future__ import annotations

import pytest

from amc.core.oidc import role_from_groups

pytestmark = pytest.mark.unit


class TestRoleFromGroups:
    """Authentik groups map to app roles with admin > coach > student."""

    def test_admin_group_wins(self) -> None:
        assert role_from_groups(["amc-admin", "amc-staff"]) == "admin"

    def test_staff_group_maps_to_coach(self) -> None:
        assert role_from_groups(["amc-staff"]) == "coach"

    def test_other_groups_default_to_student(self) -> None:
        assert role_from_groups(["some-other-group"]) == "student"
        assert role_from_groups([]) == "student"

    def test_matching_is_case_insensitive(self) -> None:
        assert role_from_groups(["AMC-Admin"]) == "admin"
        assert role_from_groups([" Amc-Staff "]) == "coach"


class TestOidcMounting:
    """The OIDC router is not part of the default app surface."""

    def test_disabled_by_default(self) -> None:
        from amc.main import create_app

        app = create_app()
        paths = {route.path for route in app.routes}  # type: ignore[attr-defined]
        assert not any("/oidc/" in path for path in paths)


class TestOidcStubsRespond:
    """The stub routes return a clear 500 (ConfigurationError) until wired up.

    Mount the OIDC router directly so the behaviour is asserted without toggling
    the process-global settings or reloading modules.
    """

    async def test_login_and_callback_stubs_return_500(self) -> None:
        from fastapi import FastAPI
        from httpx import ASGITransport, AsyncClient

        from amc.api.oidc import router as oidc_router
        from amc.main import _register_exception_handlers

        app = FastAPI()
        _register_exception_handlers(app)
        app.include_router(oidc_router, prefix="/api/v1")

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as client:
            login = await client.get("/api/v1/auth/oidc/login")
            callback = await client.get("/api/v1/auth/oidc/callback")

        assert login.status_code == 500
        assert login.json()["error"] == "ConfigurationError"
        assert callback.status_code == 500
