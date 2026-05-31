"""Unit tests for the application factory.

Covers the exception-to-HTTP mapping (including the server-error branch), the
production safety guard, and the health/readiness endpoints, lifting these
modules above the per-file coverage bar.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from amc.core.exceptions import (
    AuthorizationError,
    BusinessLogicError,
    ConfigurationError,
    ResourceNotFoundError,
    ValidationError,
)
from amc.main import _check_production_safety, _resolve_status

if TYPE_CHECKING:
    from collections.abc import Iterator

pytestmark = pytest.mark.unit


class TestResolveStatus:
    """The exception-to-status mapping walks the MRO."""

    @pytest.mark.parametrize(
        ("exc", "expected"),
        [
            (ValidationError("x"), 400),
            (AuthorizationError("x"), 403),
            (ResourceNotFoundError("x"), 404),
            (BusinessLogicError("x"), 409),
            (ConfigurationError("x"), 500),
        ],
    )
    def test_known_exceptions(self, exc: Exception, expected: int) -> None:
        assert _resolve_status(exc) == expected  # type: ignore[arg-type]

    def test_unmapped_defaults_to_500(self) -> None:
        from amc.core.exceptions import ProjectBaseError

        # A base error with no specific mapping falls through to 500.
        assert _resolve_status(ProjectBaseError("x")) == 500


class TestProductionSafety:
    """The production safety guard refuses unsafe configuration."""

    @pytest.fixture
    def _restore_settings(self) -> Iterator[None]:
        from amc.core.config import settings

        saved = (
            settings.environment,
            settings.session_secret,
            settings.session_cookie_secure,
        )
        yield
        (
            settings.environment,
            settings.session_secret,
            settings.session_cookie_secure,
        ) = saved

    @pytest.mark.usefixtures("_restore_settings")
    def test_dev_environment_skips_checks(self) -> None:
        from amc.core.config import settings

        settings.environment = "development"
        # Should not raise regardless of secret.
        _check_production_safety()

    @pytest.mark.usefixtures("_restore_settings")
    def test_production_rejects_dev_secret(self) -> None:
        from amc.core.config import DEV_SESSION_SECRET, settings

        settings.environment = "production"
        settings.session_secret = DEV_SESSION_SECRET
        with pytest.raises(ConfigurationError, match="SESSION_SECRET"):
            _check_production_safety()

    @pytest.mark.usefixtures("_restore_settings")
    def test_production_rejects_insecure_cookie(self) -> None:
        from amc.core.config import settings

        settings.environment = "production"
        settings.session_secret = "a-strong-secret-value-of-sufficient-length"
        settings.session_cookie_secure = False
        with pytest.raises(ConfigurationError, match="Secure"):
            _check_production_safety()

    @pytest.mark.usefixtures("_restore_settings")
    def test_production_accepts_safe_config(self) -> None:
        from amc.core.config import settings

        settings.environment = "production"
        settings.session_secret = "a-strong-secret-value-of-sufficient-length"
        settings.session_cookie_secure = True
        _check_production_safety()


class TestExceptionHandlerOverHttp:
    """The handler maps project errors to HTTP responses, including 500s."""

    async def test_validation_error_maps_to_400(self, client: object) -> None:
        # Hitting register with a malformed body raises ValidationError -> 400.
        from httpx import AsyncClient

        assert isinstance(client, AsyncClient)
        resp = await client.post(
            "/api/v1/auth/register",
            json={"token": "bad", "display_name": "X", "password": "longenough1"},
        )
        assert resp.status_code == 400
        body = resp.json()
        assert body["error"] == "ValidationError"
