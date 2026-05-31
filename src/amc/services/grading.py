"""Exam grading service.

Pure scoring logic ported from the prototype's ``scoreTest``, per the
"Grading & Scoring Rules" section of ``docs/planning/tech-spec.md``. There is no
partial credit. The functions here take plain data (no ORM types) so they are
trivially unit-testable to 100% coverage and reusable from the seed scripts.

Scoring rules:

- ``sixpoint`` (AMC 10/12): ``score = correct*6 + blank*1.5``;
  ``max = scored_problems * 6``.
- ``count`` (AMC 8): ``score = correct``; ``max = scored_problems``.
- ``scored_problems = num_problems - len(voided)``.
- Voided problems (1-based numbers) are excluded from ``correct``, ``wrong``,
  ``blank``, and ``max``, and are surfaced as ``"void"`` in the review.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from amc.core.exceptions import ValidationError

SCORE_MODE_SIXPOINT = "sixpoint"
SCORE_MODE_COUNT = "count"

# Points awarded per correct answer and per blank in six-point mode.
_SIXPOINT_PER_CORRECT = 6.0
_SIXPOINT_PER_BLANK = 1.5


@dataclass(frozen=True)
class ReviewItem:
    """One problem's outcome in a graded review.

    Attributes:
        n: 1-based problem number.
        your: The submitted answer, or ``None`` if left blank.
        correct: The correct answer.
        ok: Whether the submitted answer was correct.
        voided: Whether the problem was voided (excluded from scoring).
    """

    n: int
    your: str | None
    correct: str
    ok: bool
    voided: bool


@dataclass(frozen=True)
class ExamScore:
    """The result of grading an exam attempt.

    Attributes:
        score: Computed score.
        max_score: Maximum achievable score for the paper.
        correct: Count of correct answers (excludes voided).
        wrong: Count of wrong answers (excludes voided).
        blank: Count of blanks (excludes voided).
        review: Per-problem review entries, in problem order.
    """

    score: float
    max_score: float
    correct: int
    wrong: int
    blank: int
    review: list[ReviewItem] = field(default_factory=list)


def _normalise_answer(raw: str | None) -> str | None:
    """Return a normalised answer letter, or ``None`` for blanks.

    Trims whitespace and upper-cases so ``" c "`` and ``"C"`` compare equal.
    Empty strings normalise to ``None`` (treated as blank).

    Args:
        raw: The submitted answer, possibly ``None`` or whitespace.

    Returns:
        The cleaned uppercase letter, or ``None`` if blank.
    """
    if raw is None:
        return None
    cleaned = raw.strip().upper()
    return cleaned or None


def score_exam(
    *,
    answer_key: list[str],
    answers: list[str | None],
    score_mode: str,
    voided: list[int] | None = None,
) -> ExamScore:
    """Grade an exam submission.

    Args:
        answer_key: Correct answers in problem order (index 0 is problem 1).
        answers: Submitted answers in problem order; ``None`` means blank. May be
            shorter than ``answer_key`` (missing trailing answers are blanks).
        score_mode: ``sixpoint`` or ``count``.
        voided: 1-based problem numbers to exclude from scoring.

    Returns:
        An :class:`ExamScore` with totals and a per-problem review.

    Raises:
        ValidationError: If ``score_mode`` is unknown, the answer key is empty,
            or ``answers`` has more entries than the answer key.
    """
    if score_mode not in {SCORE_MODE_SIXPOINT, SCORE_MODE_COUNT}:
        msg = f"Unknown score_mode: {score_mode!r}"
        raise ValidationError(msg, field="score_mode", value=score_mode)
    if not answer_key:
        msg = "answer_key must not be empty"
        raise ValidationError(msg, field="answer_key")
    if len(answers) > len(answer_key):
        msg = "answers has more entries than the answer key"
        raise ValidationError(
            msg,
            field="answers",
            details={"answers": len(answers), "answer_key": len(answer_key)},
        )

    voided_set = {n for n in (voided or []) if 1 <= n <= len(answer_key)}

    correct = 0
    wrong = 0
    blank = 0
    review: list[ReviewItem] = []

    for index, key in enumerate(answer_key):
        number = index + 1
        key_norm = key.strip().upper()
        is_voided = number in voided_set
        # ``answers`` may be shorter than the key: treat missing as blank.
        submitted = _normalise_answer(answers[index] if index < len(answers) else None)

        if is_voided:
            review.append(
                ReviewItem(
                    n=number, your=submitted, correct=key_norm, ok=False, voided=True
                )
            )
            continue

        if submitted is None:
            blank += 1
            is_ok = False
        elif submitted == key_norm:
            correct += 1
            is_ok = True
        else:
            wrong += 1
            is_ok = False

        review.append(
            ReviewItem(
                n=number, your=submitted, correct=key_norm, ok=is_ok, voided=False
            )
        )

    scored_problems = len(answer_key) - len(voided_set)
    if score_mode == SCORE_MODE_SIXPOINT:
        score = correct * _SIXPOINT_PER_CORRECT + blank * _SIXPOINT_PER_BLANK
        max_score = scored_problems * _SIXPOINT_PER_CORRECT
    else:  # SCORE_MODE_COUNT
        score = float(correct)
        max_score = float(scored_problems)

    return ExamScore(
        score=score,
        max_score=max_score,
        correct=correct,
        wrong=wrong,
        blank=blank,
        review=review,
    )
