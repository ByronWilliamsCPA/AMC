"""Exam and Problem entities (AMC contest content).

An :class:`Exam` is one AMC paper; it owns an ordered set of :class:`Problem`
rows. ``Problem.correct_answer`` is the answer key and is *never* serialized in a
pre-submission API response; see ``amc.schemas.exam`` for the read models that
enforce this structurally.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from amc.models.base import Base, uuid_pk

if TYPE_CHECKING:
    from amc.models.attempt import TestAttempt

# Scoring modes (see tech-spec "Grading & Scoring Rules").
SCORE_MODE_SIXPOINT = "sixpoint"  # AMC 10/12: correct*6 + blank*1.5
SCORE_MODE_COUNT = "count"  # AMC 8: score == correct
VALID_SCORE_MODES = frozenset({SCORE_MODE_SIXPOINT, SCORE_MODE_COUNT})

# Problem render modes.
RENDER_MODE_LATEX = "latex"
RENDER_MODE_IMAGE = "image"
VALID_RENDER_MODES = frozenset({RENDER_MODE_LATEX, RENDER_MODE_IMAGE})


class Exam(Base):
    """One AMC paper.

    Attributes:
        id: Primary key.
        contest: ``AMC 8`` | ``AMC 10`` | ``AMC 12``.
        year: Contest year.
        variant: ``A`` or ``B`` (empty for papers without a variant).
        duration_sec: Time limit in seconds.
        score_mode: ``sixpoint`` or ``count``.
        num_problems: Number of problems on the paper.
        voided: 1-based problem numbers excluded from scoring.
        source_url: AoPS Wiki URL the answer key was sourced from.
    """

    __tablename__ = "exams"
    __table_args__ = (
        UniqueConstraint("contest", "year", "variant", name="uq_exam_identity"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    contest: Mapped[str] = mapped_column(String(20), index=True)
    year: Mapped[int] = mapped_column(Integer)
    variant: Mapped[str] = mapped_column(String(2), default="")
    duration_sec: Mapped[int] = mapped_column(Integer)
    score_mode: Mapped[str] = mapped_column(String(20))
    num_problems: Mapped[int] = mapped_column(Integer)
    # JSON list of 1-based problem numbers. Defaults to an empty list; the
    # default factory avoids the shared-mutable-default pitfall.
    voided: Mapped[list[int]] = mapped_column(JSON, default=list)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    problems: Mapped[list[Problem]] = relationship(
        back_populates="exam",
        cascade="all, delete-orphan",
        order_by="Problem.number",
    )
    attempts: Mapped[list[TestAttempt]] = relationship(
        back_populates="exam",
        cascade="all, delete-orphan",
    )


class Problem(Base):
    """A single problem on an exam.

    Attributes:
        id: Primary key.
        exam_id: Owning exam.
        number: 1-based position on the paper.
        render_mode: ``latex`` or ``image``.
        body_latex: Problem statement in LaTeX (latex mode).
        image_path: Asset-relative image path (image mode).
        choices: Answer choices for latex mode, e.g.
            ``[{"L": "A", "html": "..."}]``.
        correct_answer: ``A``..``E``. Answer key; never sent pre-submission.
        solution_url: Optional link to a worked solution.
    """

    __tablename__ = "problems"
    __table_args__ = (UniqueConstraint("exam_id", "number", name="uq_problem_number"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    exam_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("exams.id", ondelete="CASCADE"), index=True
    )
    number: Mapped[int] = mapped_column(Integer)
    render_mode: Mapped[str] = mapped_column(String(10))
    body_latex: Mapped[str | None] = mapped_column(String, nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    choices: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON, nullable=True, default=None
    )
    correct_answer: Mapped[str] = mapped_column(String(1))
    solution_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    exam: Mapped[Exam] = relationship(back_populates="problems")
