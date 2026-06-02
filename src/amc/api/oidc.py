"""OIDC / Authentik SSO routes (mounted only when ``settings.oidc_enabled``).

These endpoints are intentionally stubs: the built-in invite + password auth is
the active scheme, and SSO is deferred. When you enable OIDC, fill in the
Authorization Code exchange here (e.g. with ``authlib``) and, on a successful
callback, create a session exactly as ``amc.api.auth.login`` does and map the
``groups`` claim with :func:`amc.core.oidc.role_from_groups`.

Returning 501 (rather than silently 404) makes the not-yet-wired state explicit
if someone points Authentik at the app before the flow is implemented. The
router is only included by the app factory when ``oidc_enabled`` is true, so it
never affects the default deployment.
"""

from __future__ import annotations

from fastapi import APIRouter

from amc.core.exceptions import ConfigurationError

router = APIRouter(prefix="/auth/oidc", tags=["auth"])

_NOT_IMPLEMENTED = (
    "OIDC/Authentik SSO is enabled in config but not yet implemented. "
    "See docs/auth/authentik.md for the integration plan."
)


@router.get("/login")
async def oidc_login() -> None:
    """Begin the OIDC Authorization Code flow (stub).

    Raises:
        ConfigurationError: Always, until the flow is implemented. Mapped to a
            500 by the app's exception handler.
    """
    raise ConfigurationError(_NOT_IMPLEMENTED, details={"step": "authorize"})


@router.get("/callback")
async def oidc_callback() -> None:
    """Handle the OIDC redirect callback (stub).

    Raises:
        ConfigurationError: Always, until the flow is implemented.
    """
    raise ConfigurationError(_NOT_IMPLEMENTED, details={"step": "callback"})
