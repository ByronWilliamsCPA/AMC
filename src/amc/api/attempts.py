"""Attempt routes: submit exams and diagnostics for server-side grading.

These endpoints are the only place answer keys are used (server-side) and the
only place they are revealed (in the post-submission review). Submitting persists
the graded attempt so it is available cross-device.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from amc.api.deps import CurrentUser, DbSession
from amc.core.exceptions import ResourceNotFoundError
from amc.repositories.attempts import (
    DiagnosticAttemptRepository,
    TestAttemptRepository,
)
from amc.repositories.catalog import DiagnosticRepository, ExamRepository
from amc.schemas.diagnostic import (
    DiagnosticItemReview,
    DiagnosticResultResponse,
    DiagnosticSubmission,
)
from amc.schemas.exam import (
    ExamResultResponse,
    ExamSubmission,
    ReviewItemResponse,
)
from amc.services import diagnostics as diag_service
from amc.services.grading import score_exam

router = APIRouter(tags=["attempts"])


@router.post("/exams/{exam_id}/attempts", response_model=ExamResultResponse)
async def submit_exam(
    exam_id: uuid.UUID,
    payload: ExamSubmission,
    user: CurrentUser,
    db: DbSession,
) -> ExamResultResponse:
    """Grade and store an exam submission, returning the reviewed result.

    Args:
        exam_id: The exam being submitted.
        payload: The student's answers, flags, and time used.
        user: The authenticated submitting user.
        db: The request-scoped database session.

    Returns:
        The graded result, including the per-problem review with answers.

    Raises:
        ResourceNotFoundError: If the exam does not exist.
    """
    exam = await ExamRepository(db).get_with_problems(exam_id)
    if exam is None:
        raise ResourceNotFoundError("Exam not found", resource_type="Exam")

    ordered = sorted(exam.problems, key=lambda p: p.number)
    answer_key = [p.correct_answer for p in ordered]
    score = score_exam(
        answer_key=answer_key,
        answers=payload.answers,
        score_mode=exam.score_mode,
        voided=exam.voided,
    )

    attempt = await TestAttemptRepository(db).record(
        user_id=user.id,
        exam_id=exam.id,
        answers=payload.answers,
        flags=payload.flags,
        time_used_sec=payload.time_used_sec,
        score=score,
    )
    await db.commit()

    review = [
        ReviewItemResponse(
            n=item.n,
            your=item.your,
            correct=item.correct,
            ok=item.ok,
            voided=item.voided,
        )
        for item in score.review
    ]
    return ExamResultResponse(
        attempt_id=attempt.id,
        score=score.score,
        max_score=score.max_score,
        correct=score.correct,
        wrong=score.wrong,
        blank=score.blank,
        review=review,
    )


@router.post(
    "/diagnostics/{instrument_id}/attempts",
    response_model=DiagnosticResultResponse,
)
async def submit_diagnostic(
    instrument_id: str,
    payload: DiagnosticSubmission,
    user: CurrentUser,
    db: DbSession,
) -> DiagnosticResultResponse:
    """Grade and store a diagnostic submission, returning the verdict.

    Auto-graded items are checked server-side; manual items use the student's
    self-mark. The verdict is recomputed from the instrument's grading config.

    Args:
        instrument_id: The instrument being submitted.
        payload: The student's responses, self-marks, and elapsed time.
        user: The authenticated submitting user.
        db: The request-scoped database session.

    Returns:
        The graded result, including verdict and per-item review.

    Raises:
        ResourceNotFoundError: If the instrument does not exist.
    """
    instrument = await DiagnosticRepository(db).get_with_items(instrument_id)
    if instrument is None:
        raise ResourceNotFoundError(
            "Diagnostic not found", resource_type="DiagnosticInstrument"
        )

    graded_items: list[diag_service.GradedItem] = []
    review: list[DiagnosticItemReview] = []
    for item in instrument.items:
        item_key = str(item.id)
        if item.manual:
            correct = bool(payload.marks.get(item_key, False))
        else:
            submitted = payload.responses.get(item_key, "")
            correct = diag_service.check_auto(
                submitted, value=item.numeric_value, accept=item.accept
            )
        graded_items.append(
            diag_service.GradedItem(item_id=item_key, group=item.group, correct=correct)
        )
        review.append(
            DiagnosticItemReview(
                item_id=item_key,
                correct=correct,
                manual=item.manual,
                answer=item.answer,
            )
        )

    verdict = diag_service.grade_diagnostic(
        graded_items=graded_items, grading=instrument.grading
    )
    summary = _summary_line(instrument.course, verdict)
    attempt = await DiagnosticAttemptRepository(db).record(
        user_id=user.id,
        instrument_id=instrument.id,
        responses=dict(payload.responses),
        marks=dict(payload.marks),
        passed=verdict.passed,
        verdict=verdict.verdict,
        summary=summary,
        elapsed_sec=payload.elapsed_sec,
    )
    await db.commit()

    return DiagnosticResultResponse(
        attempt_id=attempt.id,
        passed=verdict.passed,
        verdict=verdict.verdict,
        correct=verdict.correct,
        total=verdict.total,
        summary=summary,
        group_scores=verdict.group_scores,
        review=review,
    )


def _summary_line(course: str, verdict: diag_service.DiagnosticVerdict) -> str:
    """Build a human-readable summary line for a diagnostic result.

    Args:
        course: The instrument's course.
        verdict: The computed verdict.

    Returns:
        A score line plus pass/fail phrasing.
    """
    state = "passed" if verdict.passed else "did not pass"
    return f"{course}: {verdict.correct}/{verdict.total} correct — {state}."
