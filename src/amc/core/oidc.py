"""Authentik / OIDC scaffolding (optional, disabled by default).

The active authentication scheme is the built-in invite + Argon2 + server-side
session flow in ``amc.api.auth``. This module is the *ready-to-enable* path for
SSO against a locally hosted Authentik, per the decision to defer adoption.

When enabled (``settings.oidc_enabled``), the intended design is a
backend-for-frontend (BFF) Authorization Code flow: FastAPI performs the code
exchange and mints the **same** :class:`~amc.models.user.Session` the rest of the
app already understands, so tokens never reach the browser and the cookie / RBAC
/ ``/auth/me`` / SPA layers are unchanged. Only identity verification moves to
Authentik.

Roles are derived from Authentik groups (groups -> roles), implemented by the
pure :func:`role_from_groups` below so it can be unit-tested without a running
IdP. The HTTP callback is a documented stub until the flow is wired up; see
``docs/auth/authentik.md``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from amc.core.config import settings
from amc.models import ROLE_ADMIN, ROLE_COACH, ROLE_STUDENT

if TYPE_CHECKING:
    from collections.abc import Iterable


def role_from_groups(groups: Iterable[str]) -> str:
    """Map a user's Authentik groups to an application role.

    Precedence is admin > coach > student: membership in the configured admin
    group grants ``admin``; the staff group grants ``coach``; anyone else is a
    ``student``. Group names are matched case-insensitively.

    Args:
        groups: The group names from the user's OIDC ``groups`` claim.

    Returns:
        One of ``admin`` / ``coach`` / ``student``.
    """
    normalised = {g.strip().lower() for g in groups}
    if settings.oidc_admin_group.lower() in normalised:
        return ROLE_ADMIN
    if settings.oidc_staff_group.lower() in normalised:
        return ROLE_COACH
    return ROLE_STUDENT
