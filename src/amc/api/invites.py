"""Invite minting routes (coach/admin only)."""

from __future__ import annotations

from fastapi import APIRouter

from amc.api.deps import DbSession, StaffUser
from amc.core.config import settings
from amc.core.exceptions import ValidationError
from amc.core.security import generate_invite_token
from amc.repositories.users import InviteRepository
from amc.schemas.auth import InviteCreatedResponse, InviteCreateRequest

router = APIRouter(prefix="/invites", tags=["invites"])


@router.post("", response_model=InviteCreatedResponse, status_code=201)
async def create_invite(
    payload: InviteCreateRequest, staff: StaffUser, db: DbSession
) -> InviteCreatedResponse:
    """Mint a one-time invite token (coach/admin only).

    The raw token is returned exactly once for the issuer to share; only its hash
    is stored.

    Args:
        payload: The invitee email and role to grant.
        staff: The authenticated coach/admin issuing the invite.
        db: The request-scoped database session.

    Returns:
        The created invite including the one-time raw token.

    Raises:
        ValidationError: If the requested role is invalid.
    """
    try:
        role = payload.validated_role()
    except ValueError as exc:
        raise ValidationError(str(exc), field="role") from exc

    raw_token = generate_invite_token()
    invite = await InviteRepository(db).create(
        raw_token=raw_token,
        email=payload.email,
        role=role,
        created_by=staff.id,
        ttl_seconds=settings.invite_ttl_seconds,
    )
    await db.commit()
    return InviteCreatedResponse(token=raw_token, email=invite.email, role=invite.role)
