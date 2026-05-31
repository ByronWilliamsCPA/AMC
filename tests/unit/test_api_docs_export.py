"""Tests for the API docs exporter and a drift guard for the committed artifacts.

Ensures the exporter produces a valid OpenAPI schema and Postman collection, and
that the committed ``docs/api/*`` files match what the current app generates so
the Newman monitor never runs against a stale contract.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.export_api_docs import build_collection

pytestmark = pytest.mark.unit

_DOCS_DIR = Path(__file__).resolve().parents[2] / "docs" / "api"


class TestExporter:
    """The collection builder produces a valid Postman v2.1 document."""

    def test_collection_is_valid_v21(self) -> None:
        from amc.main import create_app

        collection = build_collection(create_app().openapi())
        assert "v2.1.0" in collection["info"]["schema"]
        assert collection["item"], "collection has requests"
        # Every request carries at least one test script.
        for item in collection["item"]:
            assert item["event"], f"{item['name']} has no test event"
            exec_lines = item["event"][0]["script"]["exec"]
            assert any("pm.test" in line for line in exec_lines)

    def test_collection_has_login_and_key_guard(self) -> None:
        from amc.main import create_app

        collection = build_collection(create_app().openapi())
        names = {item["name"] for item in collection["item"]}
        assert "Auth: login" in names
        # The exam listing must assert the answer key is not exposed.
        exams = next(i for i in collection["item"] if i["name"] == "Catalog: list exams")
        script = "\n".join(exams["event"][0]["script"]["exec"])
        assert "correct_answer" in script


class TestCommittedArtifactsInSync:
    """The committed docs/api files match the current app (drift guard)."""

    def test_openapi_matches_app(self) -> None:
        from amc.main import create_app

        committed_path = _DOCS_DIR / "openapi.json"
        if not committed_path.exists():
            pytest.skip("openapi.json not exported yet")
        committed = json.loads(committed_path.read_text(encoding="utf-8"))
        current = create_app().openapi()
        assert committed["paths"].keys() == current["paths"].keys(), (
            "docs/api/openapi.json is stale; run scripts/export_api_docs.py"
        )

    def test_collection_request_paths_match_app(self) -> None:
        from amc.main import create_app

        committed_path = _DOCS_DIR / "amc.postman_collection.json"
        if not committed_path.exists():
            pytest.skip("collection not exported yet")
        committed = json.loads(committed_path.read_text(encoding="utf-8"))
        current = build_collection(create_app().openapi())
        committed_names = [i["name"] for i in committed["item"]]
        current_names = [i["name"] for i in current["item"]]
        assert committed_names == current_names, (
            "docs/api/amc.postman_collection.json is stale; "
            "run scripts/export_api_docs.py"
        )
