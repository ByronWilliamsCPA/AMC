"""Catalog routes: list and fetch exams and diagnostics without answer keys.

Every response is built from the key-free read schemas in ``amc.schemas``; the
ORM objects (which carry the keys) never reach the serializer, so a pre-submission
response cannot leak ``correct_answer`` / ``answer``.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from amc.api.deps import CurrentUser, DbSession
from amc.core.exceptions import ResourceNotFoundError
from amc.repositories.catalog import DiagnosticRepository, ExamRepository
from amc.schemas.diagnostic import (
    DiagnosticDetail,
    DiagnosticItemRead,
    DiagnosticSummary,
)
from amc.schemas.exam import ExamDetail, ExamSummary, ProblemRead

router = APIRouter(tags=["catalog"])


@router.get("/exams", response_model=list[ExamSummary])
async def list_exams(
    _user: CurrentUser, db: DbSession, contest: str | None = None
) -> list[ExamSummary]:
    """List available exams, optionally filtered by contest.

    Args:
        _user: The authenticated user (auth required).
        db: The request-scoped database session.
        contest: Optional contest filter (e.g. ``AMC 10``).

    Returns:
        Exam summaries.
    """
    exams = await ExamRepository(db).list_exams(contest=contest)
    return [ExamSummary.model_validate(e, from_attributes=True) for e in exams]


@router.get("/exams/{exam_id}", response_model=ExamDetail)
async def get_exam(exam_id: uuid.UUID, _user: CurrentUser, db: DbSession) -> ExamDetail:
    """Return an exam and its problems, without the answer key.

    Args:
        exam_id: The exam id.
        _user: The authenticated user (auth required).
        db: The request-scoped database session.

    Returns:
        The exam detail with key-free problems.

    Raises:
        ResourceNotFoundError: If the exam does not exist.
    """
    exam = await ExamRepository(db).get_with_problems(exam_id)
    if exam is None:
        raise ResourceNotFoundError("Exam not found", resource_type="Exam")

    problems = [
        ProblemRead(
            number=p.number,
            render_mode=p.render_mode,
            body_latex=p.body_latex,
            image_path=p.image_path,
            choices=p.choices,
        )
        for p in exam.problems
    ]
    return ExamDetail(
        id=exam.id,
        contest=exam.contest,
        year=exam.year,
        variant=exam.variant,
        duration_sec=exam.duration_sec,
        score_mode=exam.score_mode,
        num_problems=exam.num_problems,
        voided=exam.voided,
        problems=problems,
    )


@router.get("/diagnostics", response_model=list[DiagnosticSummary])
async def list_diagnostics(
    _user: CurrentUser, db: DbSession
) -> list[DiagnosticSummary]:
    """List available diagnostic instruments.

    Args:
        _user: The authenticated user (auth required).
        db: The request-scoped database session.

    Returns:
        Diagnostic summaries.
    """
    instruments = await DiagnosticRepository(db).list_instruments()
    return [
        DiagnosticSummary.model_validate(i, from_attributes=True) for i in instruments
    ]


@router.get("/diagnostics/{instrument_id}", response_model=DiagnosticDetail)
async def get_diagnostic(
    instrument_id: str, _user: CurrentUser, db: DbSession
) -> DiagnosticDetail:
    """Return a diagnostic instrument and its items, without answers.

    Args:
        instrument_id: The instrument slug.
        _user: The authenticated user (auth required).
        db: The request-scoped database session.

    Returns:
        The instrument detail with key-free items.

    Raises:
        ResourceNotFoundError: If the instrument does not exist.
    """
    instrument = await DiagnosticRepository(db).get_with_items(instrument_id)
    if instrument is None:
        raise ResourceNotFoundError(
            "Diagnostic not found", resource_type="DiagnosticInstrument"
        )

    items = [
        DiagnosticItemRead(
            id=item.id,
            section_title=item.section_title,
            label=item.label,
            prompt=item.prompt,
            manual=item.manual,
        )
        for item in sorted(instrument.items, key=lambda i: i.label)
    ]
    return DiagnosticDetail(
        id=instrument.id,
        course=instrument.course,
        kind=instrument.kind,
        role=instrument.role,
        instructions=instrument.instructions,
        items=items,
    )
