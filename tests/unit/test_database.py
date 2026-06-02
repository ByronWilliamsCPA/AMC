"""Unit tests for the async database helpers.

Covers URL normalisation, the session context manager's commit/rollback
behaviour, and engine lifecycle, which are otherwise only exercised indirectly.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

import amc.core.database as db_module
from amc.core.database import normalise_async_url


class TestNormaliseUrl:
    """Database URL driver normalisation."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("given", "expected"),
        [
            ("postgresql://u@h/db", "postgresql+asyncpg://u@h/db"),
            ("sqlite:///./x.db", "sqlite+aiosqlite:///./x.db"),
            ("postgresql+asyncpg://u@h/db", "postgresql+asyncpg://u@h/db"),
            ("sqlite+aiosqlite:///./x.db", "sqlite+aiosqlite:///./x.db"),
            ("mysql://u@h/db", "mysql://u@h/db"),
        ],
    )
    def test_normalisation(self, given: str, expected: str) -> None:
        assert normalise_async_url(given) == expected


class TestSessionLifecycle:
    """The engine/session helpers against an isolated in-memory database."""

    @pytest.fixture(autouse=True)
    def _isolate_engine(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Point the module at a fresh in-memory database per test."""
        monkeypatch.setattr(
            db_module.settings, "database_url", "sqlite+aiosqlite:///:memory:"
        )
        db_module._engine = None
        db_module._sessionmaker = None

    async def test_create_all_and_session_commit(self) -> None:
        await db_module.create_all()
        async with db_module.get_session() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar_one() == 1
        await db_module.dispose_engine()

    async def test_get_session_rolls_back_on_error(self) -> None:
        async def _raise_inside_session() -> None:
            async with db_module.get_session():
                error_message = "boom"
                raise RuntimeError(error_message)

        await db_module.create_all()
        with pytest.raises(RuntimeError, match="boom"):
            await _raise_inside_session()
        await db_module.dispose_engine()

    async def test_get_db_dependency_yields_session(self) -> None:
        await db_module.create_all()
        agen = db_module.get_db()
        session = await agen.__anext__()
        result = await session.execute(text("SELECT 1"))
        assert result.scalar_one() == 1
        await agen.aclose()
        await db_module.dispose_engine()
