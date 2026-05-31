"""SQLAlchemy ORM models for AMC.

Importing this package registers every mapper on ``Base.metadata`` so that
``create_all`` and Alembic autogenerate see all tables.
"""

from __future__ import annotations

from amc.models.attempt import DiagnosticAttempt, TestAttempt
from amc.models.base import Base
from amc.models.diagnostic import (
    GRADING_MODE_FUNDPS,
    GRADING_MODE_THRESHOLD,
    DiagnosticInstrument,
    DiagnosticItem,
)
from amc.models.exam import (
    RENDER_MODE_IMAGE,
    RENDER_MODE_LATEX,
    SCORE_MODE_COUNT,
    SCORE_MODE_SIXPOINT,
    VALID_RENDER_MODES,
    VALID_SCORE_MODES,
    Exam,
    Problem,
)
from amc.models.user import (
    ROLE_ADMIN,
    ROLE_COACH,
    ROLE_STUDENT,
    VALID_ROLES,
    Invite,
    Session,
    User,
)

__all__ = [
    "GRADING_MODE_FUNDPS",
    "GRADING_MODE_THRESHOLD",
    "RENDER_MODE_IMAGE",
    "RENDER_MODE_LATEX",
    "ROLE_ADMIN",
    "ROLE_COACH",
    "ROLE_STUDENT",
    "SCORE_MODE_COUNT",
    "SCORE_MODE_SIXPOINT",
    "VALID_RENDER_MODES",
    "VALID_ROLES",
    "VALID_SCORE_MODES",
    "Base",
    "DiagnosticAttempt",
    "DiagnosticInstrument",
    "DiagnosticItem",
    "Exam",
    "Invite",
    "Problem",
    "Session",
    "TestAttempt",
    "User",
]
