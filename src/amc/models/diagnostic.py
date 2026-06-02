"""Diagnostic instrument and item entities (AoPS placement content).

A :class:`DiagnosticInstrument` is one AoPS "Are You Ready?" / "Do You Know?"
questionnaire. ``ladder`` and ``grading`` are stored as JSON so the
recommendation engine can stay data-driven over the prototype's structure
without hard-coding course names. ``DiagnosticItem.answer`` is the key and is
never serialized pre-submission.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import JSON, Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from amc.models.base import Base, uuid_pk

# Grading modes carried inside ``DiagnosticInstrument.grading["mode"]``.
GRADING_MODE_THRESHOLD = "threshold"  # single ``need`` cut-off
GRADING_MODE_FUNDPS = "fundps"  # separate fundamentals / problem-solving cuts

# Catalog gate kinds carried in ``DiagnosticCatalogEntry.gate`` (CONSTANTS.md §3).
GATE_DIAGNOSTIC = "diagnostic"  # placed by a diagnostic instrument
GATE_PREREQ = "prereq"  # placed by a prerequisite course (no diagnostic)
GATE_AMC = "amc"  # unlocked by an AMC-10 score at or above ``min_score``


class DiagnosticInstrument(Base):
    """One AoPS placement instrument.

    The ``id`` is a human-readable slug (e.g. ``pa1-pre``) matching the
    prototype's instrument keys, so seeded content and recommendation logic line
    up without a translation table.

    Attributes:
        id: Slug primary key (e.g. ``pa1-pre``).
        course: Course the instrument belongs to (e.g. ``Prealgebra 1``).
        kind: ``Are You Ready?`` or ``Do You Know?``.
        role: ``AYR`` or ``DYK``.
        ladder: Prev/self/next course labels for the recommendation walk.
        grading: Mode plus thresholds (``need`` / ``fundNeeded`` / ``psNeeded``).
        instructions: Free-text instructions shown before the questionnaire.
    """

    __tablename__ = "diagnostic_instruments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    course: Mapped[str] = mapped_column(String(120))
    kind: Mapped[str] = mapped_column(String(40))
    role: Mapped[str] = mapped_column(String(8))
    ladder: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    grading: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    instructions: Mapped[str] = mapped_column(String, default="")

    items: Mapped[list[DiagnosticItem]] = relationship(
        back_populates="instrument",
        cascade="all, delete-orphan",
    )


class DiagnosticItem(Base):
    """A single question within a diagnostic instrument.

    The answer-key fields (``answer``, ``numeric_value``, ``accept``) are never
    serialized in a pre-submission response; the read schema omits them.

    Attributes:
        id: Primary key.
        instrument_id: Owning instrument slug.
        section_title: Heading grouping related items.
        label: Short label/number shown to the user.
        prompt: Question text (may contain LaTeX).
        answer: Canonical displayed answer (the contract's ``ans``).
        numeric_value: Numeric value for auto-grading (the contract's ``v``), or
            ``None`` for non-numeric/symbolic items.
        accept: Accepted string forms for auto-grading (the contract's ``accept``).
        group: ``fund`` or ``ps`` for ``fundps`` grading, else ``None``.
        manual: True when the item is symbolic and must be self-marked.
    """

    __tablename__ = "diagnostic_items"

    id: Mapped[uuid.UUID] = uuid_pk()
    instrument_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("diagnostic_instruments.id", ondelete="CASCADE"),
        index=True,
    )
    section_title: Mapped[str] = mapped_column(String(200), default="")
    label: Mapped[str] = mapped_column(String(40), default="")
    prompt: Mapped[str] = mapped_column(String, default="")
    answer: Mapped[str] = mapped_column(String, default="")
    numeric_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    accept: Mapped[list[str]] = mapped_column(JSON, default=list)
    group: Mapped[str | None] = mapped_column(String(8), nullable=True)
    manual: Mapped[bool] = mapped_column(Boolean, default=False)

    instrument: Mapped[DiagnosticInstrument] = relationship(back_populates="items")


class DiagnosticCatalogEntry(Base):
    """One row of the course catalog (``diag_data.json`` ``catalog``).

    The catalog is the placement engine's reference table: each course is reached
    by a diagnostic, a prerequisite, or an AMC-10 score gate. Only ``gate``-``amc``
    rows carry a ``min_score``; the recommendation service reads them to build the
    advisory "unlocked by your AMC 10 score" list (CONSTANTS.md §3). ``course`` is
    the natural primary key because the synthesize step joins courses by exact
    string, and each course appears once in the catalog.

    Attributes:
        course: Course name; matches instrument/ladder course strings exactly.
        gate: How the course is reached (``diagnostic``, ``prereq``, or ``amc``).
        min_score: Inclusive AMC-10 score that unlocks the course; ``None`` unless
            ``gate`` is ``amc``.
        note: Advisory text shown alongside the course.
    """

    __tablename__ = "diagnostic_catalog"

    course: Mapped[str] = mapped_column(String(120), primary_key=True)
    gate: Mapped[str] = mapped_column(String(16))
    min_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    note: Mapped[str] = mapped_column(String, default="")
