"""Exam catalog and attempt schemas.

The read models here have no field that could carry an answer key: ``ProblemRead``
omits ``correct_answer`` entirely, so a pre-submission exam payload is incapable
of leaking the key. The key is revealed only in :class:`ReviewItemResponse`,
which is built from the grading service *after* a submission.
"""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


class ExamSummary(BaseModel):
    """An exam in a catalog listing (no problems)."""

    id: uuid.UUID
    contest: str
    year: int
    variant: str
    duration_sec: int
    score_mode: str
    num_problems: int


class ProblemRead(BaseModel):
    """A problem as served before submission.

    Note the deliberate absence of any ``correct_answer`` field.
    """

    number: int
    render_mode: str
    body_latex: str | None = None
    image_path: str | None = None
    choices: list[dict[str, Any]] | None = None


class ExamDetail(BaseModel):
    """An exam with its problems, served before submission (no answer key)."""

    id: uuid.UUID
    contest: str
    year: int
    variant: str
    duration_sec: int
    score_mode: str
    num_problems: int
    voided: list[int]
    problems: list[ProblemRead]


class ExamSubmission(BaseModel):
    """A student's exam submission."""

    answers: list[str | None]
    flags: list[bool] = Field(default_factory=list)
    time_used_sec: int = Field(default=0, ge=0)


class ReviewItemResponse(BaseModel):
    """One problem's post-submission review (answer key revealed here)."""

    n: int
    your: str | None
    correct: str
    ok: bool
    voided: bool


class ExamResultResponse(BaseModel):
    """The graded result of an exam submission."""

    attempt_id: uuid.UUID
    score: float
    max_score: float
    correct: int
    wrong: int
    blank: int
    review: list[ReviewItemResponse]


class TestAttemptSummary(BaseModel):
    """A persisted exam attempt in a user's history."""

    id: uuid.UUID
    exam_id: uuid.UUID
    score: float
    max_score: float
    correct: int
    wrong: int
    blank: int
    time_used_sec: int
