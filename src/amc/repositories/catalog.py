"""Repositories for exam and diagnostic catalog content.

Read-mostly access to exams, problems, and diagnostic instruments. The API layer
is responsible for stripping answer keys before serialization; these repositories
return full ORM objects for server-side grading.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from amc.models import DiagnosticInstrument, Exam

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession


class ExamRepository:
    """Data access for :class:`~amc.models.exam.Exam` and its problems."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: The active async database session.
        """
        self._session = session

    async def list_exams(self, *, contest: str | None = None) -> list[Exam]:
        """Return exams, optionally filtered by contest, without problems loaded.

        Args:
            contest: Optional contest filter (e.g. ``AMC 10``).

        Returns:
            Matching exams ordered by year then contest.
        """
        stmt = select(Exam).order_by(Exam.year.desc(), Exam.contest, Exam.variant)
        if contest is not None:
            stmt = stmt.where(Exam.contest == contest)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_problems(self, exam_id: uuid.UUID) -> Exam | None:
        """Return an exam with its problems eagerly loaded, or ``None``.

        Args:
            exam_id: The exam id.

        Returns:
            The exam with ``problems`` populated, or ``None`` if not found.
        """
        stmt = (
            select(Exam).where(Exam.id == exam_id).options(selectinload(Exam.problems))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class DiagnosticRepository:
    """Data access for diagnostic instruments and their items."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: The active async database session.
        """
        self._session = session

    async def list_instruments(self) -> list[DiagnosticInstrument]:
        """Return all diagnostic instruments without items loaded.

        Returns:
            Instruments ordered by course then role.
        """
        stmt = select(DiagnosticInstrument).order_by(
            DiagnosticInstrument.course, DiagnosticInstrument.role
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_items(self, instrument_id: str) -> DiagnosticInstrument | None:
        """Return an instrument with its items eagerly loaded, or ``None``.

        Args:
            instrument_id: The instrument slug.

        Returns:
            The instrument with ``items`` populated, or ``None``.
        """
        stmt = (
            select(DiagnosticInstrument)
            .where(DiagnosticInstrument.id == instrument_id)
            .options(selectinload(DiagnosticInstrument.items))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
