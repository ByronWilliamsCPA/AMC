#!/usr/bin/env python3
"""Export the OpenAPI schema and a Newman-ready Postman collection.

Produces two artifacts under ``docs/api/``:

- ``openapi.json`` — the app's OpenAPI 3.1 schema, importable into Postman or
  any API client.
- ``amc.postman_collection.json`` — a Postman v2.1 collection that chains the
  core flow (login -> catalog -> submit -> progress) with monitoring assertions
  (status code, response latency, JSON validity, and the answer-key
  non-exposure guarantee). Run it with Newman for synthetic monitoring.

Usage::

    uv run python scripts/export_api_docs.py
    # then, for monitoring:
    newman run docs/api/amc.postman_collection.json \
        --env-var base_url=https://amc.example.com \
        --env-var email=coach@example.com --env-var password=secret
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from amc.main import create_app

_OUT_DIR = Path("docs/api")
_BASE_URL_VAR = "{{base_url}}"

# Reusable Postman test snippets (JavaScript executed by Newman).
_TEST_STATUS_OK = [
    "pm.test('status is 2xx', function () {",
    "  pm.expect(pm.response.code).to.be.within(200, 299);",
    "});",
]
_TEST_LATENCY = [
    "pm.test('response time under 800ms', function () {",
    "  pm.expect(pm.response.responseTime).to.be.below(800);",
    "});",
]
_TEST_JSON = [
    "pm.test('response is JSON', function () {",
    "  pm.response.to.be.json;",
    "});",
]


def _event(script_lines: list[str]) -> dict[str, Any]:
    """Wrap test script lines in a Postman event object.

    Args:
        script_lines: JavaScript lines for the test script.

    Returns:
        A Postman ``event`` entry for the ``test`` phase.
    """
    return {
        "listen": "test",
        "script": {"type": "text/javascript", "exec": script_lines},
    }


def _request(
    name: str,
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
    tests: list[str] | None = None,
    auth_capture: bool = False,
) -> dict[str, Any]:
    """Build a Postman request item.

    Args:
        name: Display name of the request.
        method: HTTP method.
        path: URL path (appended to ``{{base_url}}``).
        body: Optional JSON body.
        tests: Extra test-script lines appended to the standard checks.
        auth_capture: Whether to capture an id from the JSON response into a
            collection variable (used to chain requests).

    Returns:
        A Postman collection item.
    """
    raw_url = f"{_BASE_URL_VAR}{path}"
    request: dict[str, Any] = {
        "method": method,
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "url": {"raw": raw_url, "host": [_BASE_URL_VAR], "path": path.strip("/").split("/")},
    }
    if body is not None:
        request["body"] = {"mode": "raw", "raw": json.dumps(body, indent=2)}

    script = [*_TEST_STATUS_OK, *_TEST_LATENCY]
    if tests:
        script += ["", *tests]
    if auth_capture:
        script += [
            "",
            "var json = pm.response.json();",
            "if (json && json.id) { pm.collectionVariables.set('user_id', json.id); }",
        ]
    return {"name": name, "event": [_event(script)], "request": request}


def build_collection(schema: dict[str, Any]) -> dict[str, Any]:
    """Build a Postman v2.1 collection that monitors the core flow.

    Args:
        schema: The app's OpenAPI schema (for the info block).

    Returns:
        A Postman collection dictionary.
    """
    key_guard = [
        "pm.test('no answer key in pre-submission payload', function () {",
        "  pm.expect(pm.response.text()).to.not.include('correct_answer');",
        "  pm.expect(pm.response.text()).to.not.include('\"answer\"');",
        "});",
    ]
    items = [
        _request(
            "Health: live",
            "GET",
            "/health/live",
            tests=[
                *_TEST_JSON,
                "pm.test('status ok', function () {",
                "  pm.expect(pm.response.json().status).to.eql('ok');",
                "});",
            ],
        ),
        _request(
            "Auth: login",
            "POST",
            "/api/v1/auth/login",
            body={"email": "{{email}}", "password": "{{password}}"},
            tests=[
                *_TEST_JSON,
                "pm.test('session cookie set', function () {",
                "  pm.expect(pm.cookies.has('amc_session')).to.be.true;",
                "});",
            ],
            auth_capture=True,
        ),
        _request(
            "Auth: me",
            "GET",
            "/api/v1/auth/me",
            tests=[
                *_TEST_JSON,
                "pm.test('returns an email', function () {",
                "  pm.expect(pm.response.json()).to.have.property('email');",
                "});",
            ],
        ),
        _request(
            "Catalog: list exams",
            "GET",
            "/api/v1/exams",
            tests=[*_TEST_JSON, *key_guard],
        ),
        _request(
            "Catalog: list diagnostics",
            "GET",
            "/api/v1/diagnostics",
            tests=[
                *_TEST_JSON,
                *key_guard,
                "pm.test('diagnostics are a list', function () {",
                "  pm.expect(pm.response.json()).to.be.an('array');",
                "});",
            ],
        ),
        _request(
            "Progress: mine",
            "GET",
            "/api/v1/progress",
            tests=[
                *_TEST_JSON,
                "pm.test('has recommendation fields', function () {",
                "  var j = pm.response.json();",
                "  pm.expect(j).to.have.property('recommendation_reason');",
                "  pm.expect(j).to.have.property('test_attempts');",
                "});",
            ],
        ),
        _request("Auth: logout", "POST", "/api/v1/auth/logout"),
    ]

    return {
        "info": {
            "name": "AMC Trainer API",
            "description": (
                schema.get("info", {}).get("description", "")
                + "\n\nGenerated by scripts/export_api_docs.py. Monitors the core "
                "login -> catalog -> progress flow with status, latency, JSON, and "
                "answer-key non-exposure assertions for Newman-based synthetic "
                "monitoring."
            ),
            "schema": (
                "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            ),
        },
        "item": items,
        "variable": [
            {"key": "base_url", "value": "http://127.0.0.1:8000"},
            {"key": "email", "value": "coach@example.com"},
            {"key": "password", "value": "change-me"},
            {"key": "user_id", "value": ""},
        ],
    }


def main() -> None:
    """Write the OpenAPI schema and Postman collection to ``docs/api/``."""
    app = create_app()
    schema = app.openapi()

    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    openapi_path = _OUT_DIR / "openapi.json"
    with openapi_path.open("w", encoding="utf-8") as handle:
        json.dump(schema, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    collection = build_collection(schema)
    collection_path = _OUT_DIR / "amc.postman_collection.json"
    with collection_path.open("w", encoding="utf-8") as handle:
        json.dump(collection, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    print(f"Wrote {openapi_path} ({len(schema['paths'])} paths)")
    print(f"Wrote {collection_path} ({len(collection['item'])} requests)")


if __name__ == "__main__":
    main()
