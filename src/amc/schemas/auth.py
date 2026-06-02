"""Auth and invite request/response schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field

from amc.models import VALID_ROLES


class LoginRequest(BaseModel):
    """Credentials for starting a session."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=1024)


class RegisterRequest(BaseModel):
    """Invite redemption: set a password and create the account."""

    token: str = Field(min_length=1, max_length=512)
    display_name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=8, max_length=1024)


class InviteCreateRequest(BaseModel):
    """Request to mint a one-time invite (coach/admin only)."""

    email: EmailStr
    role: str = Field(default="student")

    def validated_role(self) -> str:
        """Return the role if valid, else raise.

        Returns:
            The validated role string.

        Raises:
            ValueError: If the role is not a recognised role.
        """
        if self.role not in VALID_ROLES:
            msg = f"role must be one of {sorted(VALID_ROLES)}"
            raise ValueError(msg)
        return self.role


class InviteCreatedResponse(BaseModel):
    """The freshly minted invite; ``token`` is shown exactly once."""

    token: str
    email: EmailStr
    role: str


class InviteValidationResponse(BaseModel):
    """Public validation result for an invite token."""

    valid: bool
    email: EmailStr | None = None
    role: str | None = None


class UserResponse(BaseModel):
    """A user, safe to return to the authenticated client."""

    id: uuid.UUID
    email: EmailStr
    display_name: str
    role: str
