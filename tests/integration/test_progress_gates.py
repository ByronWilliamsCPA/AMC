"""The progress endpoint sources AMC-10 score gates from the seeded catalog.

Before the catalog was seeded and wired, ``_build_progress`` passed an empty
gate list to ``synthesize`` and the advisory "unlocked by your AMC 10 score"
list was always empty. These tests pin the wired behaviour: a stored AMC-10
score unlocks exactly the catalog courses whose ``min`` it clears.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from amc.api.progress import _build_progress
from amc.core.security import hash_password
from amc.models import Exam, TestAttempt, User
from amc.seed import seed_catalog

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.integration

_DIAG_PATH = Path(__file__).resolve().parents[2] / "content" / "diag_data.json"


async def _student_with_amc10_score(db_session: AsyncSession, score: float) -> User:
    """Create a student with one graded AMC-10 attempt at ``score``.

    Args:
        db_session: The per-test database session.
        score: The AMC-10 score to record on the attempt.

    Returns:
        The persisted student user.
    """
    user = User(
        email="student@example.com",
        display_name="Student",
        role="student",
        password_hash=hash_password("student-password-123"),
    )
    db_session.add(user)
    exam = Exam(
        contest="AMC 10",
        year=2020,
        variant="A",
        duration_sec=4500,
        score_mode="sixpoint",
        num_problems=25,
        voided=[],
        source_url=None,
    )
    db_session.add(exam)
    await db_session.flush()
    db_session.add(
        TestAttempt(user_id=user.id, exam_id=exam.id, score=score, max_score=150.0)
    )
    await db_session.flush()
    return user


async def test_score_unlocks_only_cleared_gates(db_session: AsyncSession) -> None:
    with _DIAG_PATH.open(encoding="utf-8") as handle:
        await seed_catalog(db_session, json.load(handle))
    user = await _student_with_amc10_score(db_session, 72.0)

    progress = await _build_progress(user.id, db_session)

    # 72 clears the 60 gate (Problem Series) but not the 80 gate (Final Fives).
    assert "AMC 10 Problem Series" in progress.unlocked_by_amc
    assert "AMC 10 Final Fives" not in progress.unlocked_by_amc


async def test_high_score_unlocks_both_gates(db_session: AsyncSession) -> None:
    with _DIAG_PATH.open(encoding="utf-8") as handle:
        await seed_catalog(db_session, json.load(handle))
    user = await _student_with_amc10_score(db_session, 95.0)

    progress = await _build_progress(user.id, db_session)

    assert progress.unlocked_by_amc == [
        "AMC 10 Problem Series",
        "AMC 10 Final Fives",
    ]
