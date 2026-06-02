"""Create the first staff account out-of-band.

Onboarding is invite-only and minting an invite requires an existing coach or
admin (see ``amc.api.invites``), so the very first staff account cannot be
created through the API. This module is that bootstrap:

    uv run python -m amc.create_admin --email coach@example.com --name "Coach"

The password is never accepted as a command-line argument: that would leak it
into shell history and the process list. It is read from the
``AMC_ADMIN_PASSWORD`` environment variable when set (for non-interactive
provisioning) or prompted for interactively with confirmation. The command
refuses to overwrite an existing account so a re-run cannot silently reset a
password.
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import os
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

from amc.core.database import dispose_engine, get_session
from amc.core.exceptions import ValidationError
from amc.core.security import hash_password
from amc.models.user import ROLE_ADMIN, ROLE_COACH
from amc.repositories.users import UserRepository
from amc.utils.logging import get_logger

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from amc.models import User

logger = get_logger(__name__)

# Match the registration flow's password floor (schemas.auth.RegisterRequest).
_MIN_PASSWORD_LENGTH = 8
# Only privileged roles are worth bootstrapping out-of-band; students self-serve
# via invites once a coach/admin exists.
_STAFF_ROLES = frozenset({ROLE_ADMIN, ROLE_COACH})
# Env-var name, not a credential; allowlisted for ruff (S105) and the scanners.
_PASSWORD_ENV = "AMC_ADMIN_PASSWORD"  # noqa: S105  # pragma: allowlist secret


@dataclass(frozen=True)
class NewStaffAccount:
    """The attributes of a staff account to bootstrap.

    Attributes:
        email: Login email (stored lower-cased by the repository).
        display_name: Human-friendly name shown in the UI.
        password: Plaintext password; hashed with Argon2 before storage.
        role: ``admin`` or ``coach`` (defaults to ``admin``).
    """

    email: str
    display_name: str
    password: str
    role: str = ROLE_ADMIN


async def create_admin(session: AsyncSession, spec: NewStaffAccount) -> User:
    """Create a staff account, refusing to overwrite an existing one.

    Args:
        session: The active database session.
        spec: The account attributes to create.

    Returns:
        The newly created user.

    Raises:
        ValidationError: If the role is not a staff role, a field is blank, the
            password is too short, or a user with the email already exists.
    """
    if spec.role not in _STAFF_ROLES:
        msg = f"Role must be one of {sorted(_STAFF_ROLES)}"
        raise ValidationError(msg, field="role", value=spec.role)
    if not spec.email or "@" not in spec.email:
        msg = "A valid email is required"
        raise ValidationError(msg, field="email", value=spec.email)
    if not spec.display_name.strip():
        msg = "A display name is required"
        raise ValidationError(msg, field="display_name")
    if len(spec.password) < _MIN_PASSWORD_LENGTH:
        msg = f"Password must be at least {_MIN_PASSWORD_LENGTH} characters"
        raise ValidationError(msg, field="password")

    users = UserRepository(session)
    if await users.get_by_email(spec.email.lower()) is not None:
        msg = "A user with that email already exists"
        raise ValidationError(msg, field="email", value=spec.email)

    return await users.create(
        email=spec.email,
        display_name=spec.display_name,
        role=spec.role,
        password_hash=hash_password(spec.password),
    )


def _resolve_password() -> str:
    """Return the admin password from the environment or an interactive prompt.

    Returns:
        The plaintext password to assign to the new account.

    Raises:
        ValidationError: If the interactive entries do not match.
    """
    from_env = os.environ.get(_PASSWORD_ENV)
    if from_env is not None:
        return from_env
    password = getpass.getpass("Admin password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        msg = "Passwords do not match"
        raise ValidationError(msg, field="password")
    return password


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Optional argument list (defaults to ``sys.argv``).

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Create the first staff (admin/coach) account out-of-band."
    )
    parser.add_argument("--email", required=True, help="Login email.")
    parser.add_argument(
        "--name", required=True, dest="display_name", help="Display name."
    )
    parser.add_argument(
        "--role",
        default=ROLE_ADMIN,
        choices=sorted(_STAFF_ROLES),
        help="Account role (default: admin).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """CLI entry point: create a staff account and log the result.

    Args:
        argv: Optional argument list.

    Raises:
        SystemExit: With code 1 if validation fails (e.g. duplicate email).
    """
    args = _parse_args(argv)

    async def _run() -> User:
        try:
            spec = NewStaffAccount(
                email=args.email,
                display_name=args.display_name,
                password=_resolve_password(),
                role=args.role,
            )
            async with get_session() as session:
                return await create_admin(session, spec)
        finally:
            await dispose_engine()

    try:
        user = asyncio.run(_run())
    except ValidationError as exc:
        # A validation failure here is operator error (e.g. duplicate email),
        # not a server fault, so report it on stderr rather than the app log.
        sys.stderr.write(f"Error: {exc}\n")
        raise SystemExit(1) from exc

    logger.info("admin_created", email=user.email, role=user.role, user_id=str(user.id))
    sys.stdout.write(f"Created {user.role} account for {user.email}\n")


if __name__ == "__main__":
    main()
