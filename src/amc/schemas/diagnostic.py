"""Diagnostic catalog and attempt schemas.

As with exams, the pre-submission item model (:class:`DiagnosticItemRead`) omits
the answer fields (``answer``, ``v``, ``accept``); only ``manual`` is exposed so
the client knows which items are self-marked. Keys are revealed only in the
post-submission review.
"""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


class DiagnosticSummary(BaseModel):
    """A diagnostic instrument in a catalog listing (no items)."""

    id: str
    course: str
    kind: str
    role: str


class DiagnosticItemRead(BaseModel):
    """A diagnostic item served before submission (no answer key).

    ``manual`` is exposed so the runner knows which items are self-marked;
    ``answer`` / ``v`` / ``accept`` are intentionally absent.
    """

    id: uuid.UUID
    section_title: str
    label: str
    prompt: str
    manual: bool


class DiagnosticDetail(BaseModel):
    """A diagnostic instrument with its items, served before submission."""

    id: str
    course: str
    kind: str
    role: str
    instructions: str
    items: list[DiagnosticItemRead]


class DiagnosticSubmission(BaseModel):
    """A student's diagnostic submission.

    Attributes:
        responses: Item id -> raw typed answer (for auto-graded items).
        marks: Item id -> bool, the student's self-marks for manual items.
        elapsed_sec: Seconds spent before submission.
    """

    responses: dict[str, str] = Field(default_factory=dict)
    marks: dict[str, bool] = Field(default_factory=dict)
    elapsed_sec: int = Field(default=0, ge=0)


class DiagnosticItemReview(BaseModel):
    """One item's post-submission review (answer revealed here)."""

    item_id: str
    correct: bool
    manual: bool
    answer: str


class DiagnosticResultResponse(BaseModel):
    """The graded result of a diagnostic submission."""

    attempt_id: uuid.UUID
    passed: bool
    verdict: str
    correct: int
    total: int
    summary: str
    group_scores: dict[str, int] = Field(default_factory=dict)
    review: list[DiagnosticItemReview] = Field(default_factory=list)


class DiagnosticAttemptSummary(BaseModel):
    """A persisted diagnostic attempt in a user's history."""

    id: uuid.UUID
    instrument_id: str
    passed: bool
    verdict: str
    summary: str


class ProgressResponse(BaseModel):
    """A user's combined progress and recommendation."""

    test_attempts: list[Any]
    diagnostic_attempts: list[Any]
    recommendation_course: str | None
    recommendation_reason: str
    unlocked_by_amc: list[str] = Field(default_factory=list)
    algebra_warning: str | None = None
