"""Unit tests for the security middleware.

Exercises the security-headers, rate-limit, and SSRF-prevention middleware plus
the ``add_security_middleware`` configurator, using small ASGI apps so each
behaviour is asserted directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from amc.middleware.security import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    SSRFPreventionMiddleware,
    add_security_middleware,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

pytestmark = pytest.mark.unit


def _app() -> FastAPI:
    """Return a tiny app with a single route for middleware tests.

    Returns:
        A FastAPI app exposing ``GET /ping``.
    """
    app = FastAPI()

    @app.get("/ping")
    async def ping() -> dict[str, str]:
        return {"pong": "ok"}

    return app


async def _client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://t") as client:
        yield client


class TestSecurityHeaders:
    """The security-headers middleware sets OWASP headers."""

    async def test_headers_present(self) -> None:
        app = _app()
        app.add_middleware(SecurityHeadersMiddleware)
        async for client in _client(app):
            resp = await client.get("/ping")
            assert resp.headers["X-Content-Type-Options"] == "nosniff"
            assert resp.headers["X-Frame-Options"] == "DENY"
            assert "Content-Security-Policy" in resp.headers
            assert resp.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
            # HSTS only on HTTPS; this request is HTTP.
            assert "Strict-Transport-Security" not in resp.headers

    async def test_hsts_on_https(self) -> None:
        app = _app()
        app.add_middleware(SecurityHeadersMiddleware)
        async for client in _client(app):
            resp = await client.get("https://t/ping")
            assert "Strict-Transport-Security" in resp.headers


class TestRateLimit:
    """The rate-limit middleware blocks once the per-minute budget is spent."""

    async def test_blocks_over_limit(self) -> None:
        app = _app()
        # Tiny limit so the test is fast; burst high enough not to trip first.
        app.add_middleware(RateLimitMiddleware, requests_per_minute=3, burst_size=100)
        async for client in _client(app):
            codes = [(await client.get("/ping")).status_code for _ in range(5)]
            assert codes[:3] == [200, 200, 200]
            assert codes[3] == 429
            assert codes[4] == 429

    async def test_burst_limit(self) -> None:
        app = _app()
        app.add_middleware(RateLimitMiddleware, requests_per_minute=1000, burst_size=2)
        async for client in _client(app):
            codes = [(await client.get("/ping")).status_code for _ in range(4)]
            # The burst (per-second) ceiling trips before the per-minute one.
            assert 429 in codes

    def test_cleanup_prunes_stale_entries(self) -> None:
        import time

        mw = RateLimitMiddleware(_app(), requests_per_minute=60, cleanup_interval=0)
        # Seed a stale entry well outside the 60s window.
        mw.requests["1.2.3.4"] = [time.time() - 120]
        mw.requests["5.6.7.8"] = [time.time()]
        mw._cleanup_stale_entries(time.time())
        assert "1.2.3.4" not in mw.requests
        assert "5.6.7.8" in mw.requests


class TestSsrfPrevention:
    """The SSRF middleware blocks requests carrying internal URLs."""

    @pytest.mark.parametrize(
        "value",
        [
            "http://169.254.169.254/latest/meta-data",
            "http://localhost:8000/admin",
            "http://127.0.0.1/secret",
            "file:///etc/passwd",
            "http://10.0.0.5/internal",
        ],
    )
    async def test_blocks_internal_targets(self, value: str) -> None:
        app = _app()
        app.add_middleware(SSRFPreventionMiddleware)
        async for client in _client(app):
            resp = await client.get("/ping", params={"url": value})
            assert resp.status_code == 400

    async def test_allows_public_url(self) -> None:
        app = _app()
        app.add_middleware(SSRFPreventionMiddleware)
        async for client in _client(app):
            resp = await client.get("/ping", params={"url": "https://example.com/page"})
            assert resp.status_code == 200

    async def test_allows_non_url_params(self) -> None:
        app = _app()
        app.add_middleware(SSRFPreventionMiddleware)
        async for client in _client(app):
            resp = await client.get("/ping", params={"q": "hello world"})
            assert resp.status_code == 200

    def test_private_ip_detection(self) -> None:
        assert SSRFPreventionMiddleware._is_private_ip("127.0.0.1") is True
        assert SSRFPreventionMiddleware._is_private_ip("10.0.0.1") is True
        assert SSRFPreventionMiddleware._is_private_ip("192.168.1.1") is True
        assert SSRFPreventionMiddleware._is_private_ip("8.8.8.8") is False
        assert SSRFPreventionMiddleware._is_private_ip("not-an-ip") is False

    def test_decimal_ip_obfuscation_blocked(self) -> None:
        mw = SSRFPreventionMiddleware(_app())
        # 2130706433 == 127.0.0.1
        assert mw._is_blocked_url("http://2130706433/") is True


class TestAddSecurityMiddleware:
    """The configurator wires the requested middleware onto an app."""

    async def test_defaults_apply_headers_and_rate_limit(self) -> None:
        app = _app()
        add_security_middleware(app, rate_limit_rpm=2)
        async for client in _client(app):
            first = await client.get("/ping")
            assert first.headers["X-Frame-Options"] == "DENY"
            # rpm=2 -> third request blocked.
            await client.get("/ping")
            third = await client.get("/ping")
            assert third.status_code == 429

    async def test_can_disable_rate_limit_and_ssrf(self) -> None:
        app = _app()
        add_security_middleware(
            app,
            enable_rate_limiting=False,
            enable_ssrf_prevention=False,
            allowed_hosts=["t", "testserver"],
        )
        async for client in _client(app):
            # No rate limiting: many requests all succeed.
            codes = [(await client.get("/ping")).status_code for _ in range(5)]
            assert all(code == 200 for code in codes)
