"""FastAPI application factory.

``create_app`` builds and configures the AMC application: structured logging,
correlation and security middleware, the centralized exception-to-HTTP mapping,
and the API routers. The module also exposes a module-level ``app`` for ASGI
servers (``uvicorn amc.main:app``).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from amc.api import api_router
from amc.core.config import settings
from amc.core.database import dispose_engine
from amc.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessLogicError,
    ConfigurationError,
    ProjectBaseError,
    ResourceNotFoundError,
    ValidationError,
)
from amc.middleware import CorrelationMiddleware
from amc.middleware.security import add_security_middleware
from amc.utils.logging import get_logger, setup_logging

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = get_logger(__name__)

# OpenAPI description and tag metadata, surfaced in the exported schema so the
# Postman/Newman import is self-documenting.
_API_DESCRIPTION = (
    "Server-backed AMC Trainer API.\n\n"
    "Authentication is invite-only and session-cookie based: call "
    "`POST /api/v1/auth/login` (or `/register`) to receive an HTTP-only "
    "`amc_session` cookie, which authorises the protected endpoints. Answer "
    "keys are never present in any pre-submission response; they appear only in "
    "the graded review returned by the attempt endpoints."
)

_OPENAPI_TAGS = [
    {"name": "health", "description": "Liveness/readiness probes (unauthenticated)."},
    {"name": "auth", "description": "Login, logout, registration, and current user."},
    {"name": "invites", "description": "Mint one-time invites (coach/admin only)."},
    {"name": "catalog", "description": "Exams and diagnostics served without answer keys."},
    {"name": "attempts", "description": "Submit exams/diagnostics for server-side grading."},
    {"name": "progress", "description": "History plus the synthesized recommendation."},
]

# Statuses at or above this are server faults (logged with stack context).
_SERVER_ERROR_THRESHOLD = 500

# Maps each project exception to the HTTP status the API should return. Mirrors
# the "Error Codes" table in docs/planning/tech-spec.md.
_EXCEPTION_STATUS: dict[type[ProjectBaseError], int] = {
    ValidationError: 400,
    AuthenticationError: 401,
    AuthorizationError: 403,
    ResourceNotFoundError: 404,
    BusinessLogicError: 409,
    ConfigurationError: 500,
}


def _resolve_status(exc: ProjectBaseError) -> int:
    """Return the HTTP status code for a project exception.

    Walks the exception's MRO so subclasses inherit their base's status when not
    explicitly mapped.

    Args:
        exc: The raised project exception.

    Returns:
        The HTTP status code to respond with; 500 if unmapped.
    """
    for exc_type, status_code in _EXCEPTION_STATUS.items():
        if isinstance(exc, exc_type):
            return status_code
    return 500


def _register_exception_handlers(app: FastAPI) -> None:
    """Attach the project exception-to-HTTP handler to the app.

    Args:
        app: The application to register handlers on.
    """

    @app.exception_handler(ProjectBaseError)
    async def _handle_project_error(  # pyright: ignore[reportUnusedFunction]
        _request: Request, exc: ProjectBaseError
    ) -> JSONResponse:
        status_code = _resolve_status(exc)
        # Server-side faults are logged with stack context; client errors are
        # expected and logged at debug level to avoid noise.
        if status_code >= _SERVER_ERROR_THRESHOLD:
            logger.error("request_failed", error=exc.to_dict(), status=status_code)
        else:
            logger.debug("request_rejected", error=exc.to_dict(), status=status_code)
        return JSONResponse(status_code=status_code, content=exc.to_dict())


def _check_production_safety() -> None:
    """Fail fast when production is misconfigured.

    Raises:
        ConfigurationError: If running in production with an unsafe session
            secret or an insecure (non-HTTPS) cookie policy.
    """
    if not settings.is_production:
        return
    if not settings.is_secret_safe:
        # #CRITICAL: Security: refuse to boot production with the dev secret;
        # otherwise session cookies are trivially forgeable.
        msg = "AMC_SESSION_SECRET must be set to a strong value in production"
        raise ConfigurationError(msg, details={"setting": "session_secret"})
    if not settings.session_cookie_secure:
        msg = "Session cookies must be Secure in production"
        raise ConfigurationError(msg, details={"setting": "session_cookie_secure"})


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan: validate config on startup, dispose engine on exit.

    Args:
        _app: The application (unused).

    Yields:
        Control back to the server for the lifetime of the application.
    """
    _check_production_safety()
    logger.info("application_startup", environment=settings.environment)
    try:
        yield
    finally:
        await dispose_engine()
        logger.info("application_shutdown")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application.

    Returns:
        A configured :class:`~fastapi.FastAPI` instance.
    """
    setup_logging(
        level=settings.log_level,
        json_logs=settings.json_logs,
        include_timestamp=settings.include_timestamp,
        include_correlation=True,
    )

    app = FastAPI(
        title="AMC Trainer API",
        version="0.1.0",
        summary="Practice AMC contests and AoPS placement diagnostics.",
        description=_API_DESCRIPTION,
        lifespan=_lifespan,
        openapi_tags=_OPENAPI_TAGS,
        contact={
            "name": "AMC Trainer",
            "url": "https://github.com/ByronWilliamsCPA/AMC",
        },
        license_info={"name": "MIT"},
    )

    # Correlation IDs first so every downstream log line and response carries one.
    app.add_middleware(CorrelationMiddleware)
    # Security middleware. CORS stays closed (empty origins): the SPA is served
    # same-origin behind the reverse proxy, so cross-origin credentials are not
    # needed. HTTPS redirect is enabled only in production.
    add_security_middleware(
        app,
        enable_https_redirect=settings.is_production,
        enable_rate_limiting=True,
        enable_ssrf_prevention=True,
    )

    _register_exception_handlers(app)

    app.include_router(api_router)

    return app


app = create_app()
