"""Configuration settings for AMC.

Settings are loaded from environment variables. Application-specific settings use
the ``AMC_`` prefix; a few deployment-conventional variables (``DATABASE_URL``,
``SESSION_SECRET``, ``ENVIRONMENT``) are also accepted without the prefix so the
shipped ``docker-compose.yml`` works unchanged.

Pydantic-settings handles parsing and validation.
"""

from __future__ import annotations

from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Sentinel used as the development session secret. The application refuses to
# start in production while this value is in effect (see ``Settings.is_secret_safe``).
# Not a real credential: its presence is treated as "unconfigured" and blocked in
# production. noqa/nosec document this for the hardcoded-password scanners.
DEV_SESSION_SECRET = "dev-insecure-change-me"  # noqa: S105  # nosec B105

# 14 days, expressed in seconds (sliding session window per the tech spec).
_FOURTEEN_DAYS_SECONDS = 14 * 24 * 60 * 60
# 7 days, expressed in seconds (default invite lifetime).
_SEVEN_DAYS_SECONDS = 7 * 24 * 60 * 60


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables.

    Attributes:
        environment: Deployment environment; gates production safety checks.
        log_level: The logging level for the application.
        json_logs: Flag to enable or disable JSON formatted logs.
        include_timestamp: Flag to include timestamps in logs.
        database_url: SQLAlchemy database URL. Synchronous Postgres URLs are
            normalised to the asyncpg driver at engine-creation time.
        db_echo: Emit SQL statements to the log (debugging only).
        session_secret: Secret key used to sign session cookies.
        session_cookie_name: Name of the session cookie.
        session_ttl_seconds: Sliding session lifetime in seconds.
        session_cookie_secure: Set the ``Secure`` flag on the session cookie.
        invite_ttl_seconds: Default lifetime of an invite token in seconds.
        login_max_attempts: Failed logins per window before rate limiting.
        login_attempt_window_seconds: Rolling window for login rate limiting.
        assets_dir: Filesystem directory holding problem image assets.
    """

    model_config = SettingsConfigDict(
        env_prefix="amc_",
        case_sensitive=False,
        extra="ignore",
    )

    # Core / observability ---------------------------------------------------
    environment: Literal["development", "test", "production"] = Field(
        default="development",
        validation_alias=AliasChoices("amc_environment", "environment"),
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    json_logs: bool = False
    include_timestamp: bool = True

    # Database ---------------------------------------------------------------
    database_url: str = Field(
        default="sqlite+aiosqlite:///./amc.db",
        validation_alias=AliasChoices("amc_database_url", "database_url"),
    )
    db_echo: bool = False

    # Sessions / auth --------------------------------------------------------
    # #CRITICAL: Security: a predictable session secret lets an attacker forge
    # session cookies. The production guard in ``is_secret_safe`` must stay wired
    # into the app factory.
    session_secret: str = Field(
        default=DEV_SESSION_SECRET,
        validation_alias=AliasChoices("amc_session_secret", "session_secret"),
    )
    session_cookie_name: str = "amc_session"
    session_ttl_seconds: int = _FOURTEEN_DAYS_SECONDS
    session_cookie_secure: bool = True
    invite_ttl_seconds: int = _SEVEN_DAYS_SECONDS

    # Login rate limiting (mitigates credential stuffing) --------------------
    login_max_attempts: int = 5
    login_attempt_window_seconds: int = 300

    # Content ----------------------------------------------------------------
    assets_dir: str = "assets"

    @property
    def is_production(self) -> bool:
        """Return whether the application is running in production.

        Returns:
            True when the environment is ``production``.
        """
        return self.environment == "production"

    @property
    def is_secret_safe(self) -> bool:
        """Return whether the session secret is acceptable for production.

        Returns:
            True when the secret differs from the development sentinel and is
            long enough to resist brute force.
        """
        return (
            self.session_secret != DEV_SESSION_SECRET and len(self.session_secret) >= 32
        )


# A single, global instance of the settings
settings = Settings()
