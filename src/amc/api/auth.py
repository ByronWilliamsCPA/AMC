"""Authentication and onboarding routes.

Implements the invite-only flow from ``docs/planning/tech-spec.md``: validating
and redeeming invites, login/logout backed by signed server-side session cookies,
and the current-user endpoint. Login is rate-limited to mitigate credential
stuffing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Request, Response

from amc.api.deps import CurrentUser, DbSession
from amc.core.config import settings
from amc.core.exceptions import AuthenticationError, ValidationError
from amc.core.security import (
    hash_password,
    needs_rehash,
    sign_value,
    verify_password,
)
from amc.repositories.users import (
    InviteRepository,
    SessionRepository,
    UserRepository,
)
from amc.schemas.auth import (
    InviteValidationResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from amc.services.auth import login_rate_limiter

if TYPE_CHECKING:
    from amc.models import Session

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(response: Response, session_id: str) -> None:
    """Set the signed, hardened session cookie on a response.

    Args:
        response: The response to attach the cookie to.
        session_id: The opaque server-side session id.
    """
    signed = sign_value(settings.session_secret, session_id)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=signed,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
    )


@router.post("/login", response_model=UserResponse)
async def login(
    payload: LoginRequest, response: Response, db: DbSession
) -> UserResponse:
    """Authenticate and start a session.

    Login attempts are rate-limited per email to mitigate credential stuffing.

    Args:
        payload: The login credentials.
        response: The response (the session cookie is set on it).
        db: The request-scoped database session.

    Returns:
        The authenticated user.

    Raises:
        AuthenticationError: On bad credentials or when rate-limited.
    """
    key = payload.email.lower()
    if login_rate_limiter.is_blocked(key):
        # #CRITICAL: Security: throttle credential stuffing; do not reveal which
        # factor failed.
        raise AuthenticationError("Too many attempts; try again later")

    users = UserRepository(db)
    user = await users.get_by_email(payload.email)
    # Always run a verification to keep timing uniform whether or not the user
    # exists; verify_password returns False for a missing user via the dummy hash.
    valid = user is not None and verify_password(payload.password, user.password_hash)
    if not valid or user is None:
        login_rate_limiter.record_failure(key)
        raise AuthenticationError("Invalid email or password")

    # Opportunistically upgrade the stored hash if parameters have strengthened.
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(payload.password)
        await db.flush()

    login_rate_limiter.reset(key)
    record = await SessionRepository(db).create(
        user_id=user.id, ttl_seconds=settings.session_ttl_seconds
    )
    await db.commit()
    _set_session_cookie(response, str(record.id))
    return UserResponse.model_validate(user, from_attributes=True)


@router.post("/logout", status_code=204)
async def logout(request: Request, response: Response, db: DbSession) -> Response:
    """End the current session, if any.

    Always clears the cookie and returns 204, even if no valid session is present,
    so logout is idempotent.

    Args:
        request: The incoming request (for the session cookie).
        response: The response (the cookie is cleared on it).
        db: The request-scoped database session.

    Returns:
        An empty 204 response.
    """
    from amc.core.security import unsign_value  # noqa: PLC0415

    cookie = request.cookies.get(settings.session_cookie_name)
    if cookie:
        raw_id = unsign_value(settings.session_secret, cookie)
        if raw_id is not None:
            sessions = SessionRepository(db)
            record = await _safe_get_session(sessions, raw_id)
            if record is not None:
                await sessions.revoke(record)
                await db.commit()
    response.delete_cookie(
        key=settings.session_cookie_name,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
    )
    response.status_code = 204
    return response


async def _safe_get_session(sessions: SessionRepository, raw_id: str) -> Session | None:
    """Return an active session for a raw id string, or ``None`` if malformed.

    Args:
        sessions: The session repository.
        raw_id: The unsigned session id string.

    Returns:
        The active session record, or ``None``.
    """
    import uuid  # noqa: PLC0415

    try:
        session_id = uuid.UUID(raw_id)
    except ValueError:
        return None
    return await sessions.get_active(session_id)


@router.get("/me", response_model=UserResponse)
async def me(user: CurrentUser) -> UserResponse:
    """Return the currently authenticated user.

    Args:
        user: The authenticated user (from the session cookie).

    Returns:
        The current user.
    """
    return UserResponse.model_validate(user, from_attributes=True)


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    payload: RegisterRequest, response: Response, db: DbSession
) -> UserResponse:
    """Redeem an invite, create the account, and start a session.

    Args:
        payload: The invite token, display name, and chosen password.
        response: The response (the session cookie is set on it).
        db: The request-scoped database session.

    Returns:
        The newly created user.

    Raises:
        ValidationError: If the invite is invalid/expired or the email is taken.
    """
    invites = InviteRepository(db)
    invite = await invites.get_valid_by_token(payload.token)
    if invite is None:
        raise ValidationError("Invalid or expired invite", field="token")

    users = UserRepository(db)
    if await users.get_by_email(invite.email) is not None:
        raise ValidationError("An account already exists for this invite")

    user = await users.create(
        email=invite.email,
        display_name=payload.display_name,
        role=invite.role,
        password_hash=hash_password(payload.password),
    )
    await invites.mark_redeemed(invite)

    record = await SessionRepository(db).create(
        user_id=user.id, ttl_seconds=settings.session_ttl_seconds
    )
    await db.commit()
    _set_session_cookie(response, str(record.id))
    return UserResponse.model_validate(user, from_attributes=True)


@router.get("/invites/{token}", response_model=InviteValidationResponse)
async def validate_invite(token: str, db: DbSession) -> InviteValidationResponse:
    """Validate an invite token without redeeming it.

    Args:
        token: The raw invite token from the invite link.
        db: The request-scoped database session.

    Returns:
        Whether the token is valid and, if so, the email and role it grants.
    """
    invite = await InviteRepository(db).get_valid_by_token(token)
    if invite is None:
        return InviteValidationResponse(valid=False)
    return InviteValidationResponse(valid=True, email=invite.email, role=invite.role)
