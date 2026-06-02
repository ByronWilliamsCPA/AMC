"""Attempt entities: persisted results of taking an exam or a diagnostic.

A :class:`TestAttempt` records a graded AMC paper submission; a
:class:`DiagnosticAttempt` records a graded placement questionnaire. Both belong
to a user and are the durable, cross-device history that is the product's core
value.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from amc.models.base import Base, created_at_column, uuid_pk

if TYPE_CHECKING:
    from amc.models.exam import Exam
    from amc.models.user import User


class TestAttempt(Base):
    """A graded AMC paper submission.

    Attributes:
        id: Primary key.
        user_id: Owning user.
        exam_id: Exam that was attempted.
        started_at: When the runner was opened.
        submitted_at: When the attempt was submitted/graded.
        answers: Per-problem submitted answers (``None`` for blank), in order.
        flags: Per-problem flag state, in order.
        time_used_sec: Seconds spent before submission.
        score: Computed score.
        correct: Number of correct answers (excludes voided).
        wrong: Number of wrong answers (excludes voided).
        blank: Number of blanks (excludes voided).
        max_score: Maximum achievable score for the paper.
        created_at: Row creation timestamp.
    """

    __tablename__ = "test_attempts"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    exam_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("exams.id", ondelete="CASCADE"), index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    answers: Mapped[list[str | None]] = mapped_column(JSON, default=list)
    flags: Mapped[list[bool]] = mapped_column(JSON, default=list)
    time_used_sec: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    correct: Mapped[int] = mapped_column(Integer, default=0)
    wrong: Mapped[int] = mapped_column(Integer, default=0)
    blank: Mapped[int] = mapped_column(Integer, default=0)
    max_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = created_at_column()

    user: Mapped[User] = relationship(back_populates="test_attempts")
    exam: Mapped[Exam] = relationship(back_populates="attempts")


class DiagnosticAttempt(Base):
    """A graded placement-diagnostic submission.

    Attributes:
        id: Primary key.
        user_id: Owning user.
        instrument_id: Instrument that was attempted.
        submitted_at: When the attempt was submitted/graded.
        responses: Item id -> raw submitted input.
        marks: Item id -> bool for self-marked (manual) items.
        passed: Whether the instrument's pass threshold was met.
        verdict: ``win`` | ``mid`` | ``low``.
        summary: Score line plus recommendation message.
        elapsed_sec: Seconds spent before submission.
        created_at: Row creation timestamp.
    """

    __tablename__ = "diagnostic_attempts"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    instrument_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("diagnostic_instruments.id", ondelete="CASCADE"),
        index=True,
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    responses: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    marks: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    verdict: Mapped[str] = mapped_column(String(8), default="")
    summary: Mapped[str] = mapped_column(String, default="")
    elapsed_sec: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = created_at_column()

    user: Mapped[User] = relationship(back_populates="diagnostic_attempts")
