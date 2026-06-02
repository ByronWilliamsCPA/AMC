"""Tests for the out-of-band staff-account bootstrap (``amc.create_admin``).

Covers the core ``create_admin`` guard rails, the password resolver's env and
interactive branches, argument parsing, and the CLI entry point end to end
against a throwaway SQLite database.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from amc.core.exceptions import ValidationError
from amc.core.security import verify_password
from amc.create_admin import (
    NewStaffAccount,
    _parse_args,
    _resolve_password,
    create_admin,
)
from amc.repositories.users import UserRepository

if TYPE_CHECKING:
    from pathlib import Path

    from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.integration

# Test fixture, not a real credential.
_PASSWORD = "bootstrap-pw-123"  # pragma: allowlist secret


class TestCreateAdmin:
    """Core account creation and its guard rails."""

    async def test_creates_admin_by_default(self, db_session: AsyncSession) -> None:
        user = await create_admin(
            db_session,
            NewStaffAccount(
                email="Coach@Example.com", display_name="Coach", password=_PASSWORD
            ),
        )
        assert user.role == "admin"
        # Email is normalised to lower case and the hash verifies.
        assert user.email == "coach@example.com"
        assert verify_password(_PASSWORD, user.password_hash)
        # The plaintext is never stored.
        assert _PASSWORD not in user.password_hash

    async def test_creates_coach_role(self, db_session: AsyncSession) -> None:
        user = await create_admin(
            db_session,
            NewStaffAccount(
                email="c@example.com",
                display_name="C",
                password=_PASSWORD,
                role="coach",
            ),
        )
        assert user.role == "coach"

    async def test_rejects_duplicate_email(self, db_session: AsyncSession) -> None:
        await create_admin(
            db_session,
            NewStaffAccount(
                email="a@example.com", display_name="A", password=_PASSWORD
            ),
        )
        with pytest.raises(ValidationError, match="already exists"):
            await create_admin(
                db_session,
                NewStaffAccount(
                    email="a@example.com", display_name="A2", password=_PASSWORD
                ),
            )
        # The duplicate attempt did not create a second row.
        assert await UserRepository(db_session).count() == 1

    async def test_rejects_short_password(self, db_session: AsyncSession) -> None:
        with pytest.raises(ValidationError, match="at least 8"):
            await create_admin(
                db_session,
                NewStaffAccount(
                    email="a@example.com",
                    display_name="A",
                    password="short",  # pragma: allowlist secret
                ),
            )

    async def test_rejects_non_staff_role(self, db_session: AsyncSession) -> None:
        with pytest.raises(ValidationError, match="Role must be"):
            await create_admin(
                db_session,
                NewStaffAccount(
                    email="a@example.com",
                    display_name="A",
                    password=_PASSWORD,
                    role="student",
                ),
            )

    async def test_rejects_blank_name(self, db_session: AsyncSession) -> None:
        with pytest.raises(ValidationError, match="display name"):
            await create_admin(
                db_session,
                NewStaffAccount(
                    email="a@example.com", display_name="   ", password=_PASSWORD
                ),
            )

    async def test_rejects_invalid_email(self, db_session: AsyncSession) -> None:
        with pytest.raises(ValidationError, match="valid email"):
            await create_admin(
                db_session,
                NewStaffAccount(
                    email="not-an-email", display_name="A", password=_PASSWORD
                ),
            )


class TestResolvePassword:
    """The password resolver: env var vs interactive prompt."""

    def test_reads_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AMC_ADMIN_PASSWORD", "from-env-123")
        assert _resolve_password() == "from-env-123"

    def test_prompts_when_env_absent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("AMC_ADMIN_PASSWORD", raising=False)
        monkeypatch.setattr("getpass.getpass", lambda _prompt: "typed-pw-123")
        assert _resolve_password() == "typed-pw-123"

    def test_rejects_mismatched_confirmation(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("AMC_ADMIN_PASSWORD", raising=False)
        answers = iter(["first-pw-123", "second-pw-456"])
        monkeypatch.setattr("getpass.getpass", lambda _prompt: next(answers))
        with pytest.raises(ValidationError, match="do not match"):
            _resolve_password()


class TestParseArgs:
    """CLI argument parsing."""

    def test_defaults_to_admin(self) -> None:
        args = _parse_args(["--email", "a@example.com", "--name", "A"])
        assert args.email == "a@example.com"
        assert args.display_name == "A"
        assert args.role == "admin"

    def test_accepts_coach_role(self) -> None:
        args = _parse_args(
            ["--email", "a@example.com", "--name", "A", "--role", "coach"]
        )
        assert args.role == "coach"

    def test_missing_email_exits(self) -> None:
        with pytest.raises(SystemExit):
            _parse_args(["--name", "A"])


class TestMainCli:
    """The ``python -m amc.create_admin`` entry point against a temp SQLite file."""

    def _point_at_temp_db(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from sqlalchemy import create_engine

        import amc.core.database as db_module
        from amc.models import Base

        db_path = tmp_path / "admin.db"
        url = f"sqlite+aiosqlite:///{db_path}"
        monkeypatch.setattr(db_module.settings, "database_url", url)
        db_module._engine = None
        db_module._sessionmaker = None

        sync_engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(sync_engine)
        sync_engine.dispose()

    def test_main_creates_admin(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from sqlalchemy import create_engine, text

        from amc import create_admin as module

        self._point_at_temp_db(tmp_path, monkeypatch)
        monkeypatch.setenv("AMC_ADMIN_PASSWORD", _PASSWORD)

        module.main(["--email", "boot@example.com", "--name", "Boot"])

        check = create_engine(f"sqlite:///{tmp_path / 'admin.db'}")
        with check.connect() as conn:
            role = conn.execute(
                text("SELECT role FROM users WHERE email = 'boot@example.com'")
            ).scalar_one()
        check.dispose()
        assert role == "admin"

    def test_main_exits_on_duplicate(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from amc import create_admin as module

        self._point_at_temp_db(tmp_path, monkeypatch)
        monkeypatch.setenv("AMC_ADMIN_PASSWORD", _PASSWORD)

        module.main(["--email", "dup@example.com", "--name", "Dup"])
        # Re-running for the same email exits non-zero rather than clobbering.
        with pytest.raises(SystemExit) as exc:
            module.main(["--email", "dup@example.com", "--name", "Dup"])
        assert exc.value.code == 1
