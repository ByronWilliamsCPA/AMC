"""Async database engine, session factory, and FastAPI dependency.

A single async SQLAlchemy engine is created lazily from :data:`amc.core.config.settings`.
Two access patterns are provided:

- :func:`get_session`: an async context manager for use outside the request
  cycle (health checks, seed scripts, background jobs).
- :func:`get_db`: a FastAPI dependency that yields a request-scoped session and
  guarantees rollback on error and close on completion.

The engine is process-global and created on first use so importing this module
never opens a connection (important for tooling and tests).
"""

from __future__ import annotations

import importlib
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from amc.core.config import settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def normalise_async_url(url: str) -> str:
    """Return a database URL that uses an async driver.

    Operators commonly set ``DATABASE_URL=postgresql://...`` (the synchronous
    form). SQLAlchemy's async engine requires an async driver, so plain
    ``postgresql://`` and ``sqlite://`` URLs are upgraded to ``asyncpg`` and
    ``aiosqlite`` respectively. URLs that already name an async driver are
    returned unchanged.

    Args:
        url: The configured database URL.

    Returns:
        A URL whose dialect uses an async driver.
    """
    if url.startswith(("postgresql+", "sqlite+")):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("sqlite://"):
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return url


_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Return the process-global async engine, creating it on first use.

    Returns:
        The shared :class:`~sqlalchemy.ext.asyncio.AsyncEngine`.
    """
    global _engine  # noqa: PLW0603
    if _engine is None:
        url = normalise_async_url(settings.database_url)
        # SQLite needs check_same_thread relaxed for the async driver; Postgres
        # ignores connect_args here. pool_pre_ping avoids handing out dead
        # connections after a database restart.
        connect_args: dict[str, object] = {}
        if url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        _engine = create_async_engine(
            url,
            echo=settings.db_echo,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Return the process-global session factory, creating it on first use.

    Returns:
        An :class:`~sqlalchemy.ext.asyncio.async_sessionmaker` bound to the
        shared engine.
    """
    global _sessionmaker  # noqa: PLW0603
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _sessionmaker


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession]:
    """Yield a database session as an async context manager.

    Commits on clean exit and rolls back if the body raises. Use this outside
    the request cycle (health checks, seed scripts, background jobs). Request
    handlers should depend on :func:`get_db` instead.

    Yields:
        An active :class:`~sqlalchemy.ext.asyncio.AsyncSession`.
    """
    factory = get_sessionmaker()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db() -> AsyncGenerator[AsyncSession]:
    """FastAPI dependency that yields a request-scoped session.

    The session is rolled back if the handler raises and always closed when the
    request finishes. Handlers are responsible for committing their own writes
    so that a successful response reflects durably persisted state.

    Yields:
        An active :class:`~sqlalchemy.ext.asyncio.AsyncSession`.
    """
    factory = get_sessionmaker()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def create_all() -> None:
    """Create every table from the ORM metadata.

    Intended for tests and local SQLite bootstrapping. Production schema changes
    go through Alembic migrations, not this function.
    """
    # Import for side effects: registers all mappers on ``Base.metadata`` so
    # ``create_all`` sees every table. ``importlib`` keeps the unused-import
    # checker satisfied while making the side effect explicit.
    importlib.import_module("amc.models")

    engine = get_engine()
    async with engine.begin() as conn:
        await _run_create_all(conn)


async def _run_create_all(conn: AsyncConnection) -> None:
    """Create all tables over an async connection.

    Args:
        conn: The async connection provided by ``engine.begin``.
    """
    await conn.run_sync(Base.metadata.create_all)


async def dispose_engine() -> None:
    """Dispose the global engine and reset cached factories.

    Call on application shutdown and between tests that swap the database URL.
    """
    global _engine, _sessionmaker  # noqa: PLW0603
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None
