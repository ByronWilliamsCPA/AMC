"""FastAPI dependencies for authentication and authorization.

These wire the signed session cookie to a current :class:`~amc.models.user.User`
and enforce the role-based access rules from ``docs/planning/tech-spec.md``: a
student sees only their own data; a coach/admin may read any student's progress.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from amc.core.config import settings
from amc.core.database import get_db
from amc.core.exceptions import AuthenticationError, AuthorizationError
from amc.core.security import unsign_value
from amc.models import User
from amc.repositories.users import SessionRepository, UserRepository

# Runtime-resolvable so FastAPI can read the Depends metadata when these aliases
# annotate route/dependency parameters in other modules.
DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(request: Request, db: DbSession) -> User:
    """Return the authenticated user for the request.

    Reads the signed session cookie, validates the server-side session (existence,
    not revoked, not expired), slides its expiry, and loads the user.

    Args:
        request: The incoming request (for the session cookie).
        db: The request-scoped database session.

    Returns:
        The authenticated user.

    Raises:
        AuthenticationError: If the cookie is missing, tampered, or the session is
            invalid/expired.
    """
    cookie = request.cookies.get(settings.session_cookie_name)
    if not cookie:
        raise AuthenticationError("Not authenticated")

    raw_id = unsign_value(settings.session_secret, cookie)
    if raw_id is None:
        raise AuthenticationError("Invalid session")

    try:
        session_id = uuid.UUID(raw_id)
    except ValueError as exc:
        raise AuthenticationError("Invalid session") from exc

    sessions = SessionRepository(db)
    record = await sessions.get_active(session_id)
    if record is None:
        raise AuthenticationError("Session expired")

    await sessions.slide_expiry(record, ttl_seconds=settings.session_ttl_seconds)

    user = await UserRepository(db).get_by_id(record.user_id)
    if user is None:
        raise AuthenticationError("Session expired")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def require_staff(user: CurrentUser) -> User:
    """Return the current user, requiring a coach/admin role.

    Args:
        user: The authenticated user.

    Returns:
        The user, if they are staff.

    Raises:
        AuthorizationError: If the user is not a coach or admin.
    """
    if not user.is_staff:
        raise AuthorizationError("Staff role required")
    return user


StaffUser = Annotated[User, Depends(require_staff)]


def authorize_view_user(viewer: User, target_user_id: uuid.UUID) -> None:
    """Authorize a viewer to read a target user's data.

    A user may always read their own data; staff may read anyone's.

    Args:
        viewer: The authenticated user requesting access.
        target_user_id: The id of the user whose data is requested.

    Raises:
        AuthorizationError: If a non-staff viewer requests another user's data.
    """
    if viewer.id != target_user_id and not viewer.is_staff:
        raise AuthorizationError("Cannot access another user's data")
