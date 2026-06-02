"""Targeted tests for auth schemas and user model properties.

Covers small uncovered branches in InviteCreateRequest and User.is_staff
that are not exercised by the main HTTP fixture tests.
"""

from __future__ import annotations

import uuid

import pytest

from amc.models.user import ROLE_ADMIN, ROLE_COACH, ROLE_STUDENT, User
from amc.schemas.auth import InviteCreateRequest


class TestInviteCreateRequest:
    """InviteCreateRequest.validated_role covers the error branch."""

    @pytest.mark.unit
    def test_valid_student_role(self) -> None:
        req = InviteCreateRequest(email="a@b.com", role="student")
        assert req.validated_role() == "student"

    @pytest.mark.unit
    def test_valid_coach_role(self) -> None:
        req = InviteCreateRequest(email="a@b.com", role="coach")
        assert req.validated_role() == "coach"

    @pytest.mark.unit
    def test_invalid_role_raises(self) -> None:
        req = InviteCreateRequest(email="a@b.com", role="superuser")
        with pytest.raises(ValueError, match="role must be one of"):
            req.validated_role()


class TestUserIsStaff:
    """User.is_staff property covers the line that returns the role check."""

    def _user(self, role: str) -> User:
        return User(
            id=uuid.uuid4(),
            email="u@example.com",
            display_name="Test",
            password_hash="hash",
            role=role,
        )

    @pytest.mark.unit
    def test_student_is_not_staff(self) -> None:
        assert self._user(ROLE_STUDENT).is_staff is False

    @pytest.mark.unit
    def test_coach_is_staff(self) -> None:
        assert self._user(ROLE_COACH).is_staff is True

    @pytest.mark.unit
    def test_admin_is_staff(self) -> None:
        assert self._user(ROLE_ADMIN).is_staff is True
