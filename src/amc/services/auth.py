"""Authentication orchestration: login, registration, and rate limiting.

Keeps the routers thin and centralises the security-sensitive flow: Argon2
verification, server-side session creation, invite redemption, and an in-memory
login rate limiter that mitigates credential stuffing (the open assumption from
``docs/planning/project-vision.md``, added to Phase 1).
"""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from amc.core.config import settings


class LoginRateLimiter:
    """A simple in-memory sliding-window rate limiter keyed by identity.

    Tracks recent failed-attempt timestamps per key (email or client IP) and
    blocks once the configured threshold is exceeded within the window. Intended
    for the single-instance deployment described in ADR-001; a multi-instance
    deployment would move this to a shared store.
    """

    def __init__(self, *, max_attempts: int, window_seconds: int) -> None:
        """Initialize the limiter.

        Args:
            max_attempts: Failed attempts allowed within the window.
            window_seconds: The rolling window length in seconds.
        """
        self._max_attempts = max_attempts
        self._window_seconds = window_seconds
        self._attempts: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def is_blocked(self, key: str) -> bool:
        """Return whether a key is currently rate-limited.

        Args:
            key: The identity to check (e.g. lower-cased email).

        Returns:
            True when recent failures meet or exceed the threshold.
        """
        now = time.monotonic()
        with self._lock:
            recent = self._prune(key, now)
            return len(recent) >= self._max_attempts

    def record_failure(self, key: str) -> None:
        """Record a failed attempt for a key.

        Args:
            key: The identity that failed authentication.
        """
        now = time.monotonic()
        with self._lock:
            recent = self._prune(key, now)
            recent.append(now)
            self._attempts[key] = recent

    def reset(self, key: str) -> None:
        """Clear a key's failure history (e.g. after a successful login).

        Args:
            key: The identity to reset.
        """
        with self._lock:
            self._attempts.pop(key, None)

    def _prune(self, key: str, now: float) -> list[float]:
        """Return the key's timestamps within the window (drops stale ones).

        Args:
            key: The identity whose history to prune.
            now: The current monotonic time.

        Returns:
            The retained recent timestamps.
        """
        cutoff = now - self._window_seconds
        recent = [t for t in self._attempts.get(key, []) if t > cutoff]
        self._attempts[key] = recent
        return recent


# Process-global limiter sized from settings. The single-instance deployment
# (ADR-001) makes an in-process limiter sufficient.
login_rate_limiter = LoginRateLimiter(
    max_attempts=settings.login_max_attempts,
    window_seconds=settings.login_attempt_window_seconds,
)
