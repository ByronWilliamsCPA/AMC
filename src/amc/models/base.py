"""Shared building blocks for ORM models.

Re-exports the declarative :class:`~amc.core.database.Base` and provides small
helpers used across model modules (timezone-aware timestamps, UUID primary-key
columns).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from amc.core.database import Base

__all__ = ["Base", "created_at_column", "utcnow", "uuid_pk"]


def utcnow() -> datetime:
    """Return the current time as a timezone-aware UTC datetime.

    Returns:
        The current UTC time. Timezone-aware to satisfy strict datetime rules
        and to round-trip correctly through ``DateTime(timezone=True)`` columns.
    """
    return datetime.now(tz=UTC)


def uuid_pk() -> Mapped[uuid.UUID]:
    """Return a UUID primary-key column with a random default.

    Returns:
        A mapped column suitable as a primary key, defaulting to a fresh
        :func:`uuid.uuid4` on insert.
    """
    return mapped_column(primary_key=True, default=uuid.uuid4)


def created_at_column() -> Mapped[datetime]:
    """Return a non-null ``created_at`` column defaulting to now.

    Returns:
        A mapped, timezone-aware datetime column populated on insert.
    """
    return mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
