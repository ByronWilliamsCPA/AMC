"""Progress routes: a user's history plus the synthesized recommendation.

Assembles exam and diagnostic history and feeds the latest diagnostic results and
best AMC-10 score into the recommendation engine. A student may read only their
own progress; a coach/admin may read any student's (RBAC via ``deps``).
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from fastapi import APIRouter

from amc.api.deps import CurrentUser, DbSession, authorize_view_user
from amc.core.exceptions import ResourceNotFoundError
from amc.repositories.attempts import (
    DiagnosticAttemptRepository,
    TestAttemptRepository,
)
from amc.repositories.catalog import DiagnosticRepository, ExamRepository
from amc.repositories.users import UserRepository
from amc.schemas.diagnostic import (
    DiagnosticAttemptSummary,
    ProgressResponse,
)
from amc.schemas.exam import TestAttemptSummary
from amc.services.recommendation import (
    AmcGate,
    InstrumentResult,
    Recommendation,
    synthesize,
)

if TYPE_CHECKING:
    from amc.models import DiagnosticAttempt, DiagnosticInstrument, TestAttempt

router = APIRouter(tags=["progress"])

_AMC10_CONTEST = "AMC 10"


@router.get("/progress", response_model=ProgressResponse)
async def get_my_progress(user: CurrentUser, db: DbSession) -> ProgressResponse:
    """Return the authenticated user's progress and recommendation.

    Args:
        user: The authenticated user.
        db: The request-scoped database session.

    Returns:
        The user's history and synthesized recommendation.
    """
    return await _build_progress(user.id, db)


@router.get("/users/{user_id}/progress", response_model=ProgressResponse)
async def get_user_progress(
    user_id: uuid.UUID, viewer: CurrentUser, db: DbSession
) -> ProgressResponse:
    """Return a specific user's progress (self, or any user for staff).

    Args:
        user_id: The target user's id.
        viewer: The authenticated requesting user.
        db: The request-scoped database session.

    Returns:
        The target user's history and synthesized recommendation.

    Raises:
        AuthorizationError: If a non-staff viewer requests another user's data.
        ResourceNotFoundError: If the target user does not exist.
    """
    authorize_view_user(viewer, user_id)
    if await UserRepository(db).get_by_id(user_id) is None:
        raise ResourceNotFoundError("User not found", resource_type="User")
    return await _build_progress(user_id, db)


async def _build_progress(user_id: uuid.UUID, db: DbSession) -> ProgressResponse:
    """Assemble history and the synthesized recommendation for a user.

    Args:
        user_id: The user whose progress to build.
        db: The request-scoped database session.

    Returns:
        The assembled progress response.
    """
    test_attempts = await TestAttemptRepository(db).list_for_user(user_id)
    diag_attempts = await DiagnosticAttemptRepository(db).list_for_user(user_id)

    diagnostics = DiagnosticRepository(db)
    instruments = await diagnostics.list_instruments()
    by_id = {inst.id: inst for inst in instruments}

    ladder = _ladder_from(instruments)
    results = _latest_results(diag_attempts, by_id)
    amc10 = await _best_amc10(test_attempts, db)
    amc_gates = await _amc_gates_from(diagnostics)

    recommendation = synthesize(
        ladder=ladder,
        results=results,
        amc10_score=amc10,
        amc_gates=amc_gates,
    )
    return _to_response(test_attempts, diag_attempts, recommendation)


async def _amc_gates_from(diagnostics: DiagnosticRepository) -> list[AmcGate]:
    """Return the AMC-10 score gates from the seeded diagnostic catalog.

    The catalog's ``gate``-``amc`` rows (CONSTANTS.md §3) drive the advisory list
    of courses an AMC-10 score unlocks. Sourcing them from seeded content keeps
    the thresholds out of application code, so re-seeding changes behaviour.

    Args:
        diagnostics: The diagnostic repository bound to the request session.

    Returns:
        Catalog AMC gates as :class:`AmcGate` inputs for ``synthesize``.
    """
    entries = await diagnostics.list_amc_gates()
    return [
        AmcGate(course=entry.course, min_score=entry.min_score, note=entry.note)
        for entry in entries
        if entry.min_score is not None
    ]


def _ladder_from(instruments: list[DiagnosticInstrument]) -> list[str]:
    """Return the course ladder derived from instruments in a stable order.

    Args:
        instruments: All diagnostic instruments.

    Returns:
        Distinct course names in first-seen order.
    """
    seen: list[str] = []
    for inst in instruments:
        if inst.course not in seen:
            seen.append(inst.course)
    return seen


def _latest_results(
    diag_attempts: list[DiagnosticAttempt],
    by_id: dict[str, DiagnosticInstrument],
) -> dict[str, InstrumentResult]:
    """Build the latest-per-course-and-role result map for synthesis.

    Args:
        diag_attempts: The user's diagnostic attempts, newest first.
        by_id: Instruments keyed by slug.

    Returns:
        A mapping of ``f"{course}:{role}"`` to the latest :class:`InstrumentResult`.
    """
    results: dict[str, InstrumentResult] = {}
    for attempt in diag_attempts:
        instrument = by_id.get(attempt.instrument_id)
        if instrument is None:
            continue
        key = f"{instrument.course}:{instrument.role}"
        if key in results:
            continue  # newest-first: first seen is the latest
        results[key] = InstrumentResult(
            instrument_id=instrument.id,
            course=instrument.course,
            role=instrument.role,
            passed=attempt.passed,
            ladder={str(k): str(v) for k, v in instrument.ladder.items()},
        )
    return results


async def _best_amc10(test_attempts: list[TestAttempt], db: DbSession) -> float | None:
    """Return the user's best AMC-10 score, or ``None``.

    Args:
        test_attempts: The user's exam attempts.
        db: The request-scoped database session.

    Returns:
        The highest AMC-10 score across attempts, or ``None`` if none taken.
    """
    if not test_attempts:
        return None
    exams = ExamRepository(db)
    best: float | None = None
    cache: dict[uuid.UUID, str] = {}
    for attempt in test_attempts:
        contest = cache.get(attempt.exam_id)
        if contest is None:
            exam = await exams.get_with_problems(attempt.exam_id)
            contest = exam.contest if exam is not None else ""
            cache[attempt.exam_id] = contest
        if contest == _AMC10_CONTEST:
            best = attempt.score if best is None else max(best, attempt.score)
    return best


def _to_response(
    test_attempts: list[TestAttempt],
    diag_attempts: list[DiagnosticAttempt],
    recommendation: Recommendation,
) -> ProgressResponse:
    """Map history and a recommendation into the response schema.

    Args:
        test_attempts: The user's exam attempts.
        diag_attempts: The user's diagnostic attempts.
        recommendation: The synthesized recommendation.

    Returns:
        The progress response.
    """
    tests = [
        TestAttemptSummary(
            id=a.id,
            exam_id=a.exam_id,
            score=a.score,
            max_score=a.max_score,
            correct=a.correct,
            wrong=a.wrong,
            blank=a.blank,
            time_used_sec=a.time_used_sec,
        )
        for a in test_attempts
    ]
    diags = [
        DiagnosticAttemptSummary(
            id=a.id,
            instrument_id=a.instrument_id,
            passed=a.passed,
            verdict=a.verdict,
            summary=a.summary,
        )
        for a in diag_attempts
    ]
    return ProgressResponse(
        test_attempts=tests,
        diagnostic_attempts=diags,
        recommendation_course=recommendation.course,
        recommendation_reason=recommendation.reason,
        unlocked_by_amc=recommendation.unlocked_by_amc,
        algebra_warning=recommendation.algebra_warning,
    )
