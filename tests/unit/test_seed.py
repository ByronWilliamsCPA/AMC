"""Unit tests for the database seeding module.

Covers the pure helper functions (no database required) and the CLI
argument parser.  The async DB functions (seed_amc, seed_diag, run_seed)
are exercised by the integration suite.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from amc.seed import SeedCounts, _build_item, _build_problem, _load_json, _parse_args


class TestSeedCounts:
    """SeedCounts dataclass."""

    @pytest.mark.unit
    def test_construction_and_fields(self) -> None:
        counts = SeedCounts(exams=3, problems=90, instruments=2, items=40, catalog=10)
        assert counts.exams == 3
        assert counts.problems == 90
        assert counts.instruments == 2
        assert counts.items == 40
        assert counts.catalog == 10

    @pytest.mark.unit
    def test_zero_counts(self) -> None:
        counts = SeedCounts(exams=0, problems=0, instruments=0, items=0, catalog=0)
        assert counts.exams == 0

    @pytest.mark.unit
    def test_frozen(self) -> None:
        counts = SeedCounts(exams=1, problems=30, instruments=1, items=15, catalog=5)
        with pytest.raises(AttributeError):
            counts.exams = 99  # type: ignore[misc]


class TestLoadJson:
    """_load_json: reads a JSON file and returns the parsed object."""

    @pytest.mark.unit
    def test_reads_dict(self, tmp_path: Path) -> None:
        data = {"key": "value", "number": 42}
        f = tmp_path / "test.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        result = _load_json(f)
        assert result == data

    @pytest.mark.unit
    def test_reads_nested(self, tmp_path: Path) -> None:
        data = {"tests": {"2023": {"problems": [{"n": 1}]}}}
        f = tmp_path / "nested.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        assert _load_json(f)["tests"]["2023"]["problems"][0]["n"] == 1

    @pytest.mark.unit
    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            _load_json(tmp_path / "nonexistent.json")


class TestBuildProblem:
    """_build_problem: pure function that maps a contract dict to a Problem ORM."""

    _EXAM_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

    def _test_dict(
        self,
        answers: list[str | None] | None = None,
        mode: str = "latex",
        voided: list[int] | None = None,
    ) -> dict:
        return {
            "contest": "AMC10A",
            "year": 2023,
            "exam": "A",
            "durationSec": 4500,
            "scoreMode": "standard",
            "answers": answers if answers is not None else ["A", "B", "C", "D", "E"],
            "mode": mode,
            "voided": voided or [],
        }

    @pytest.mark.unit
    def test_latex_mode(self) -> None:
        test = self._test_dict(answers=["B"], mode="latex")
        problem = {"n": 1, "q": r"\text{What is } 2+2?", "choices": ["1", "2", "4"]}
        result = _build_problem(self._EXAM_ID, test, problem)
        assert result.exam_id == self._EXAM_ID
        assert result.number == 1
        assert result.render_mode == "latex"
        assert result.body_latex == r"\text{What is } 2+2?"
        assert result.correct_answer == "B"

    @pytest.mark.unit
    def test_image_mode(self) -> None:
        test = self._test_dict(answers=["C"], mode="img")
        problem = {"n": 1, "img": "p001.png"}
        result = _build_problem(self._EXAM_ID, test, problem)
        assert result.render_mode == "image"
        assert result.image_path == "p001.png"

    @pytest.mark.unit
    def test_answer_out_of_range_gives_empty(self) -> None:
        test = self._test_dict(answers=["A"])
        problem = {"n": 5, "q": "hard problem"}
        result = _build_problem(self._EXAM_ID, test, problem)
        assert result.correct_answer == ""

    @pytest.mark.unit
    def test_empty_answers_list(self) -> None:
        test = self._test_dict(answers=[])
        problem = {"n": 1, "q": "no key"}
        result = _build_problem(self._EXAM_ID, test, problem)
        assert result.correct_answer == ""

    @pytest.mark.unit
    def test_solution_url(self) -> None:
        test = self._test_dict(answers=["A"])
        problem = {"n": 1, "q": "q", "sol": "https://example.com/sol"}
        result = _build_problem(self._EXAM_ID, test, problem)
        assert result.solution_url == "https://example.com/sol"

    @pytest.mark.unit
    def test_choices_stored(self) -> None:
        test = self._test_dict(answers=["D"])
        problem = {"n": 1, "q": "q", "choices": ["a", "b", "c", "d", "e"]}
        result = _build_problem(self._EXAM_ID, test, problem)
        assert result.choices == ["a", "b", "c", "d", "e"]


class TestBuildItem:
    """_build_item: pure function that maps a contract dict to a DiagnosticItem ORM."""

    @pytest.mark.unit
    def test_basic_item(self) -> None:
        section = {"title": "Algebra I"}
        item = {
            "label": "alg-01",
            "prompt": r"Solve $2x = 4$.",
            "ans": "2",
            "v": 2.0,
        }
        result = _build_item("pre-algebra", section, item)
        assert result.instrument_id == "pre-algebra"
        assert result.section_title == "Algebra I"
        assert result.label == "alg-01"
        assert result.prompt == r"Solve $2x = 4$."
        assert result.answer == "2"
        assert result.numeric_value == 2.0
        assert result.manual is False

    @pytest.mark.unit
    def test_missing_optional_fields_default(self) -> None:
        result = _build_item("slug", {}, {})
        assert result.section_title == ""
        assert result.label == ""
        assert result.prompt == ""
        assert result.answer == ""
        assert result.numeric_value is None
        assert result.accept == []
        assert result.group is None

    @pytest.mark.unit
    def test_accept_list(self) -> None:
        item = {"ans": "1/2", "accept": ["0.5", ".5", "1/2"], "v": 0.5}
        result = _build_item("frac", {}, item)
        assert result.accept == ["0.5", ".5", "1/2"]

    @pytest.mark.unit
    def test_manual_flag(self) -> None:
        item = {"ans": "open-ended", "manual": True}
        result = _build_item("open", {}, item)
        assert result.manual is True

    @pytest.mark.unit
    def test_group_set(self) -> None:
        item = {"ans": "3", "group": "word-problems"}
        result = _build_item("alg", {}, item)
        assert result.group == "word-problems"


class TestParseArgs:
    """_parse_args: CLI argument parser."""

    @pytest.mark.unit
    def test_defaults(self) -> None:
        args = _parse_args([])
        assert args.amc == Path("content/amc_data.json")
        assert args.diag == Path("content/diag_data.json")

    @pytest.mark.unit
    def test_custom_paths(self) -> None:
        args = _parse_args(["--amc", "/tmp/a.json", "--diag", "/tmp/d.json"])
        assert args.amc == Path("/tmp/a.json")
        assert args.diag == Path("/tmp/d.json")

    @pytest.mark.unit
    def test_amc_only(self) -> None:
        args = _parse_args(["--amc", "custom.json"])
        assert args.amc == Path("custom.json")
        assert args.diag == Path("content/diag_data.json")
