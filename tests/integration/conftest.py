"""Fixtures for integration tests: seeded content and an authenticated client.

These build on the in-memory async database and ASGI client from the top-level
conftest, seeding a minimal but representative exam and diagnostic plus an admin
user so the API can be exercised end to end without the full content payload.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest_asyncio

from amc.core.security import hash_password
from amc.models import (
    DiagnosticInstrument,
    DiagnosticItem,
    Exam,
    Problem,
    User,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession


@pytest_asyncio.fixture
async def seeded_exam(db_session: AsyncSession) -> Exam:
    """Seed a small AMC-8 exam (count mode) with a known answer key.

    Args:
        db_session: The per-test database session.

    Returns:
        The persisted exam with three problems (key A, B, C).
    """
    exam = Exam(
        contest="AMC 8",
        year=2019,
        variant="",
        duration_sec=2400,
        score_mode="count",
        num_problems=3,
        voided=[],
        source_url=None,
    )
    db_session.add(exam)
    await db_session.flush()
    for number, key in enumerate(["A", "B", "C"], start=1):
        db_session.add(
            Problem(
                exam_id=exam.id,
                number=number,
                render_mode="latex",
                body_latex=f"Problem {number}",
                choices=[{"L": letter, "html": letter} for letter in "ABCDE"],
                correct_answer=key,
            )
        )
    await db_session.flush()
    return exam


@pytest_asyncio.fixture
async def seeded_diagnostic(db_session: AsyncSession) -> DiagnosticInstrument:
    """Seed a single-mode diagnostic with one auto and one manual item.

    Args:
        db_session: The per-test database session.

    Returns:
        The persisted instrument (pass needs 1 of 2 correct).
    """
    instrument = DiagnosticInstrument(
        id="pa1-pre",
        course="Prealgebra 1",
        kind="Are You Ready?",
        role="AYR",
        ladder={"prev": "review", "self": "Prealgebra 1", "next": "Prealgebra 2"},
        grading={"mode": "single", "total": 2, "need": 1},
        instructions="Seed instrument.",
    )
    db_session.add(instrument)
    await db_session.flush()
    db_session.add(
        DiagnosticItem(
            instrument_id=instrument.id,
            section_title="Auto",
            label="1",
            prompt="2 + 2",
            answer="4",
            numeric_value=4.0,
            accept=["4"],
            group=None,
            manual=False,
        )
    )
    db_session.add(
        DiagnosticItem(
            instrument_id=instrument.id,
            section_title="Manual",
            label="2",
            prompt="Simplify x + x",
            answer="2x",
            numeric_value=None,
            accept=[],
            group=None,
            manual=True,
        )
    )
    await db_session.flush()
    return instrument


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Seed an admin user with a known password.

    Args:
        db_session: The per-test database session.

    Returns:
        The persisted admin user (password ``admin-password-123``).
    """
    user = User(
        email="admin@example.com",
        display_name="Admin",
        role="admin",
        password_hash=hash_password("admin-password-123"),
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def admin_client(
    client: AsyncClient, admin_user: User
) -> AsyncIterator[AsyncClient]:
    """Yield a client already logged in as the admin user.

    Args:
        client: The base ASGI client.
        admin_user: The seeded admin user.

    Yields:
        The client with an active session cookie.
    """
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "admin-password-123"},
    )
    assert resp.status_code == 200, resp.text
    yield client
