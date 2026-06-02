"""Repositories for users, invites, and sessions.

Backs the invite-only authentication flow: minting and redeeming invites,
creating users, and creating/loading/revoking server-side sessions.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import select

from amc.core.security import hash_token
from amc.models import Invite, Session, User
from amc.models.base import utcnow

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository:
    """Data access for :class:`~amc.models.user.User`."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: The active async database session.
        """
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Return a user by id, or ``None``.

        Args:
            user_id: The user's id.

        Returns:
            The user, or ``None`` if not found.
        """
        return await self._session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        """Return a user by email (case-insensitive), or ``None``.

        Args:
            email: The login email.

        Returns:
            The matching user, or ``None``.
        """
        stmt = select(User).where(User.email == email.lower())
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self, *, email: str, display_name: str, role: str, password_hash: str
    ) -> User:
        """Create and persist a new user.

        Args:
            email: Unique login email (stored lower-cased).
            display_name: Human-friendly display name.
            role: One of ``student`` / ``coach`` / ``admin``.
            password_hash: Argon2 password hash.

        Returns:
            The newly created user.
        """
        user = User(
            email=email.lower(),
            display_name=display_name,
            role=role,
            password_hash=password_hash,
        )
        self._session.add(user)
        await self._session.flush()
        return user

    async def count(self) -> int:
        """Return the total number of users.

        Returns:
            The user row count (used to bootstrap the first admin).
        """
        result = await self._session.execute(select(User.id))
        return len(result.all())


class InviteRepository:
    """Data access for :class:`~amc.models.user.Invite`."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: The active async database session.
        """
        self._session = session

    async def create(
        self,
        *,
        raw_token: str,
        email: str,
        role: str,
        created_by: uuid.UUID,
        ttl_seconds: int,
    ) -> Invite:
        """Create an invite, storing only the token's hash.

        Args:
            raw_token: The high-entropy token (shared with the invitee once).
            email: The address the invite is for.
            role: Role granted on redemption.
            created_by: Issuing user's id.
            ttl_seconds: Lifetime of the invite in seconds.

        Returns:
            The persisted invite.
        """
        invite = Invite(
            token_hash=hash_token(raw_token),
            email=email.lower(),
            role=role,
            created_by=created_by,
            expires_at=utcnow() + timedelta(seconds=ttl_seconds),
        )
        self._session.add(invite)
        await self._session.flush()
        return invite

    async def get_valid_by_token(self, raw_token: str) -> Invite | None:
        """Return an unredeemed, unexpired invite for a raw token.

        Args:
            raw_token: The raw invite token.

        Returns:
            The valid invite, or ``None`` if missing, expired, or redeemed.
        """
        stmt = select(Invite).where(Invite.token_hash == hash_token(raw_token))
        result = await self._session.execute(stmt)
        invite = result.scalar_one_or_none()
        if invite is None or invite.redeemed_at is not None:
            return None
        if _aware(invite.expires_at) <= utcnow():
            return None
        return invite

    async def mark_redeemed(self, invite: Invite) -> None:
        """Mark an invite as redeemed now.

        Args:
            invite: The invite to mark.
        """
        invite.redeemed_at = utcnow()
        await self._session.flush()


class SessionRepository:
    """Data access for :class:`~amc.models.user.Session`."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: The active async database session.
        """
        self._session = session

    async def create(self, *, user_id: uuid.UUID, ttl_seconds: int) -> Session:
        """Create a server-side session row.

        Args:
            user_id: The owning user's id.
            ttl_seconds: Sliding session lifetime in seconds.

        Returns:
            The persisted session.
        """
        record = Session(
            user_id=user_id,
            expires_at=utcnow() + timedelta(seconds=ttl_seconds),
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_active(self, session_id: uuid.UUID) -> Session | None:
        """Return a non-revoked, unexpired session by id.

        Args:
            session_id: The opaque session id from the cookie.

        Returns:
            The active session, or ``None``.
        """
        record = await self._session.get(Session, session_id)
        if record is None or record.revoked:
            return None
        if _aware(record.expires_at) <= utcnow():
            return None
        return record

    async def slide_expiry(self, record: Session, *, ttl_seconds: int) -> None:
        """Extend a session's expiry to now plus the TTL.

        Args:
            record: The session to refresh.
            ttl_seconds: The sliding window in seconds.
        """
        record.expires_at = utcnow() + timedelta(seconds=ttl_seconds)
        await self._session.flush()

    async def revoke(self, record: Session) -> None:
        """Revoke a session (logout).

        Args:
            record: The session to revoke.
        """
        record.revoked = True
        await self._session.flush()


def _aware(value: datetime) -> datetime:
    """Return a timezone-aware view of a datetime read from the database.

    SQLite returns naive datetimes even for ``DateTime(timezone=True)`` columns;
    treat such values as UTC so comparisons against :func:`utcnow` are valid.

    Args:
        value: The datetime read from the database.

    Returns:
        A timezone-aware datetime (UTC assumed when naive).
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=utcnow().tzinfo)
    return value
