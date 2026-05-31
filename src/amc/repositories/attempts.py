"""Repositories for persisted exam and diagnostic attempts.

Stores graded results and reads a user's history, which is the durable,
cross-device record that is the product's core value.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from amc.models import DiagnosticAttempt, TestAttempt
from amc.models.base import utcnow

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

    from amc.services.grading import ExamScore


class TestAttemptRepository:
    """Data access for :class:`~amc.models.attempt.TestAttempt`."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: The active async database session.
        """
        self._session = session

    async def record(
        self,
        *,
        user_id: uuid.UUID,
        exam_id: uuid.UUID,
        answers: list[str | None],
        flags: list[bool],
        time_used_sec: int,
        score: ExamScore,
    ) -> TestAttempt:
        """Persist a graded exam attempt.

        Args:
            user_id: The submitting user's id.
            exam_id: The attempted exam's id.
            answers: Submitted answers in problem order.
            flags: Per-problem flag state.
            time_used_sec: Seconds spent before submission.
            score: The computed :class:`~amc.services.grading.ExamScore`.

        Returns:
            The persisted attempt.
        """
        attempt = TestAttempt(
            user_id=user_id,
            exam_id=exam_id,
            submitted_at=utcnow(),
            answers=answers,
            flags=flags,
            time_used_sec=time_used_sec,
            score=score.score,
            correct=score.correct,
            wrong=score.wrong,
            blank=score.blank,
            max_score=score.max_score,
        )
        self._session.add(attempt)
        await self._session.flush()
        return attempt

    async def list_for_user(self, user_id: uuid.UUID) -> list[TestAttempt]:
        """Return a user's exam attempts, newest first.

        Args:
            user_id: The user's id.

        Returns:
            The user's test attempts ordered by submission time descending.
        """
        stmt = (
            select(TestAttempt)
            .where(TestAttempt.user_id == user_id)
            .order_by(TestAttempt.submitted_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class DiagnosticAttemptRepository:
    """Data access for :class:`~amc.models.attempt.DiagnosticAttempt`."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: The active async database session.
        """
        self._session = session

    async def record(
        self,
        *,
        user_id: uuid.UUID,
        instrument_id: str,
        responses: dict[str, Any],
        marks: dict[str, Any],
        passed: bool,
        verdict: str,
        summary: str,
        elapsed_sec: int,
    ) -> DiagnosticAttempt:
        """Persist a graded diagnostic attempt.

        Args:
            user_id: The submitting user's id.
            instrument_id: The attempted instrument's slug.
            responses: Item id -> raw submitted input.
            marks: Item id -> bool for self-marked items.
            passed: Whether the instrument's threshold(s) were met.
            verdict: ``win`` / ``mid`` / ``low``.
            summary: Score line plus recommendation message.
            elapsed_sec: Seconds spent before submission.

        Returns:
            The persisted attempt.
        """
        attempt = DiagnosticAttempt(
            user_id=user_id,
            instrument_id=instrument_id,
            submitted_at=utcnow(),
            responses=responses,
            marks=marks,
            passed=passed,
            verdict=verdict,
            summary=summary,
            elapsed_sec=elapsed_sec,
        )
        self._session.add(attempt)
        await self._session.flush()
        return attempt

    async def list_for_user(self, user_id: uuid.UUID) -> list[DiagnosticAttempt]:
        """Return a user's diagnostic attempts, newest first.

        Args:
            user_id: The user's id.

        Returns:
            The user's diagnostic attempts ordered by submission time descending.
        """
        stmt = (
            select(DiagnosticAttempt)
            .where(DiagnosticAttempt.user_id == user_id)
            .order_by(DiagnosticAttempt.submitted_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
