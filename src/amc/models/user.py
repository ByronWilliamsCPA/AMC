"""User, Invite, and Session entities.

These three tables back the invite-only authentication flow described in
``docs/planning/tech-spec.md`` (Security): a coach mints an :class:`Invite`, the
student redeems it to create a :class:`User`, and each login creates a
server-side :class:`Session` whose opaque id is carried in a signed cookie.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from amc.models.base import Base, created_at_column, uuid_pk

if TYPE_CHECKING:
    from amc.models.attempt import DiagnosticAttempt, TestAttempt

# Role values are stored as plain strings (portable across SQLite/Postgres) and
# validated at the application boundary by the auth schemas.
ROLE_STUDENT = "student"
ROLE_COACH = "coach"
ROLE_ADMIN = "admin"
VALID_ROLES = frozenset({ROLE_STUDENT, ROLE_COACH, ROLE_ADMIN})


class User(Base):
    """A person with access to the trainer.

    Attributes:
        id: Primary key.
        email: Unique login identifier.
        display_name: Human-friendly name shown in the UI.
        role: One of ``student``, ``coach``, or ``admin``.
        password_hash: Argon2 hash of the password (never the plaintext).
        created_at: Row creation timestamp.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20), default=ROLE_STUDENT)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = created_at_column()

    test_attempts: Mapped[list[TestAttempt]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    diagnostic_attempts: Mapped[list[DiagnosticAttempt]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    @property
    def is_staff(self) -> bool:
        """Return whether the user may view other students' progress.

        Returns:
            True for coach and admin roles.
        """
        return self.role in {ROLE_COACH, ROLE_ADMIN}


class Invite(Base):
    """A one-time onboarding token granting a role on redemption.

    Only the SHA-256 hash of the token is stored; the raw token is shared with
    the invitee exactly once.

    Attributes:
        id: Primary key.
        token_hash: SHA-256 hex digest of the raw invite token (unique).
        email: Address the invite is intended for.
        role: Role granted when the invite is redeemed.
        created_by: User id of the issuing coach/admin.
        expires_at: Expiry timestamp; redemption after this is rejected.
        redeemed_at: When the invite was redeemed, or ``None`` if unused.
        created_at: Row creation timestamp.
    """

    __tablename__ = "invites"

    id: Mapped[uuid.UUID] = uuid_pk()
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(320), index=True)
    role: Mapped[str] = mapped_column(String(20), default=ROLE_STUDENT)
    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    redeemed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = created_at_column()


class Session(Base):
    """A server-side session record; the cookie carries only its id.

    Attributes:
        id: Opaque primary key, placed (signed) in the session cookie.
        user_id: Owning user.
        created_at: When the session was created.
        expires_at: Sliding expiry; refreshed on activity.
        revoked: True once logged out or revoked by staff.
    """

    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = created_at_column()
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
