"""Pytest configuration and shared fixtures for AMC tests.

This module provides:
- Test fixture paths and directories
- Pytest markers for test categorization
- Shared fixtures for common test resources
- Temporary directory management
- An isolated in-memory async database and HTTP client for API tests
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession

# ============================================================================
# Test Fixture Paths
# ============================================================================

# Root paths
PROJECT_ROOT = Path(__file__).parent.parent
FIXTURES_DIR = PROJECT_ROOT / "data" / "test_fixtures"
BENCHMARKS_DIR = PROJECT_ROOT / "data" / "benchmarks"


# ============================================================================
# Pytest Markers
# ============================================================================


def pytest_configure(config: pytest.Config) -> None:
    """Register custom pytest markers for test pyramid.

    Test Pyramid Markers:
        unit: Fast, isolated tests (no external dependencies)
        integration: Tests verifying component interaction
        security: Security-focused assertion tests
        perf: Performance and load tests
        slow: Tests that take significant time

    Args:
        config: Pytest configuration object.
    """
    # Test type markers (for test pyramid)
    config.addinivalue_line(
        "markers",
        "unit: Unit tests (fast, isolated, no external dependencies)",
    )
    config.addinivalue_line(
        "markers",
        "integration: Integration tests (moderate speed, may use fixtures)",
    )
    config.addinivalue_line(
        "markers",
        "security: Security-focused tests (auth, input validation, etc.)",
    )
    config.addinivalue_line(
        "markers",
        "perf: Performance and load tests (benchmarking, stress testing)",
    )
    config.addinivalue_line(
        "markers",
        "performance: Alias for perf marker",
    )

    # Execution modifier markers
    config.addinivalue_line(
        "markers",
        "slow: Slow tests (can be excluded with -m 'not slow')",
    )
    config.addinivalue_line(
        "markers",
        "smoke: Smoke tests for quick sanity checks",
    )
    config.addinivalue_line(
        "markers",
        "regression: Regression tests for previously fixed bugs",
    )


# ============================================================================
# Fixture Directory Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Return path to test fixtures directory.

    Returns:
        Path object pointing to the test fixtures directory.
    """
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def benchmarks_dir() -> Path:
    """Return path to benchmarks directory.

    Returns:
        Path object pointing to the benchmarks directory.
    """
    return BENCHMARKS_DIR


# ============================================================================
# Temporary Directory Fixtures
# ============================================================================


@pytest.fixture
def tmp_output_dir(tmp_path: Path) -> Path:
    """Return temporary directory for test outputs.

    Creates and returns a clean temporary directory for each test to write
    output files.

    Args:
        tmp_path: Pytest's built-in tmp_path fixture.

    Returns:
        Path object pointing to the temporary output directory.
    """
    output_dir = tmp_path / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


@pytest.fixture
def tmp_cache_dir(tmp_path: Path) -> Path:
    """Return temporary directory for caching.

    Creates and returns a clean temporary cache directory for each test.

    Args:
        tmp_path: Pytest's built-in tmp_path fixture.

    Returns:
        Path object pointing to the temporary cache directory.
    """
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir


# ============================================================================
# Logging Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def setup_logging() -> None:
    """Setup test logging configuration.

    Automatically applied to all tests to ensure consistent logging setup.
    """
    from amc.utils.logging import setup_logging

    setup_logging(level="DEBUG", json_logs=False, include_timestamp=False)


# ============================================================================
# Async Database & API Client Fixtures
# ============================================================================
#
# Tests run against a fresh in-memory SQLite database per test, using a single
# shared connection (StaticPool) so every session in the test sees the same
# schema and data. The FastAPI ``get_db`` dependency is overridden to draw from
# this engine, giving integration tests a real database without Postgres.


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Yield a session bound to a fresh in-memory database.

    A new engine and schema are created for each test and disposed afterwards,
    guaranteeing isolation regardless of test execution order.

    Yields:
        An active :class:`~sqlalchemy.ext.asyncio.AsyncSession`.
    """
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )
    from sqlalchemy.pool import StaticPool

    from amc.models import Base

    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    session = factory()
    try:
        yield session
    finally:
        await session.close()
        await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """Yield an HTTP client wired to the app with the test database.

    The app's ``get_db`` dependency is overridden to yield the per-test
    ``db_session`` so requests and assertions share one database.

    Args:
        db_session: The per-test database session fixture.

    Yields:
        An :class:`httpx.AsyncClient` bound to the ASGI app via ASGITransport.
    """
    from httpx import ASGITransport, AsyncClient

    from amc.core.database import get_db
    from amc.main import create_app

    app = create_app()

    async def _override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as http_client:
        yield http_client

    app.dependency_overrides.clear()
