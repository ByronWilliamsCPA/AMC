"""Unit tests for the diagnostic grading service.

Covers the numeric parser (integers, fractions, mixed numbers, powers,
decimals, and unparseable input), the auto-grader's equivalence and text
fallback, and both grading modes including the conservative default. Targets
100% coverage of ``amc.services.diagnostics``.
"""

import pytest

from amc.services.diagnostics import (
    GradedItem,
    check_auto,
    grade_diagnostic,
    parse_numeric,
)


class TestParseNumeric:
    """The textual-answer parser."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("text", "expected_float"),
        [
            ("42", 42.0),
            ("-7", -7.0),
            ("5/7", 5 / 7),
            ("1 3/4", 1.75),
            ("-2 1/2", -2.5),
            ("2^7", 128.0),
            ("2^-1", 0.5),
            ("0.75", 0.75),
            ("-1.5", -1.5),
        ],
    )
    def test_parses_numeric_forms(self, text: str, expected_float: float) -> None:
        value = parse_numeric(text)
        assert value is not None
        assert float(value) == pytest.approx(expected_float)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "text",
        ["", "   ", "x+1", "sqrt(2)", "5/0", "1 2/0", "0^-1", "abc"],
    )
    def test_unparseable_returns_none(self, text: str) -> None:
        assert parse_numeric(text) is None


class TestCheckAuto:
    """Numeric-tolerance and accept-list grading (CONSTANTS.md §8)."""

    @pytest.mark.unit
    def test_equivalent_fraction_and_decimal(self) -> None:
        # Submitting 0.5 against a key value of 1/2.
        assert check_auto("0.5", value=0.5) is True

    @pytest.mark.unit
    def test_power_equivalence(self) -> None:
        assert check_auto("2^3", value=8) is True

    @pytest.mark.unit
    def test_mixed_number_against_value(self) -> None:
        assert check_auto("1 3/4", value=1.75) is True

    @pytest.mark.unit
    def test_wrong_value(self) -> None:
        assert check_auto("3", value=4) is False

    @pytest.mark.unit
    def test_accept_list_matches_with_prefix_and_units(self) -> None:
        # Normalisation strips the "x=" prefix and a trailing unit word.
        assert check_auto("x = 96 miles", value=None, accept=["96"]) is True

    @pytest.mark.unit
    def test_accept_list_strips_thousands_separator(self) -> None:
        assert check_auto("3660", value=None, accept=["3,660"]) is True

    @pytest.mark.unit
    def test_accept_list_differs(self) -> None:
        assert check_auto("red", value=None, accept=["blue"]) is False

    @pytest.mark.unit
    def test_no_value_no_accept_never_correct(self) -> None:
        assert check_auto("anything", value=None, accept=[]) is False

    @pytest.mark.unit
    def test_relative_tolerance_for_non_integer_value(self) -> None:
        # 44.4 mph rounded answer; key value 44.4 -> within max(0.01, |v|*1e-4).
        assert check_auto("44.4", value=44.4) is True

    @pytest.mark.unit
    def test_numeric_accept_takes_precedence_over_value(self) -> None:
        # Even with a value set, an exact accept-list hit returns True.
        assert check_auto("2^7", value=128, accept=["2^7"]) is True

    @pytest.mark.unit
    def test_unparseable_submission_against_value_is_false(self) -> None:
        assert check_auto("x+1", value=5) is False


class TestGradeDiagnosticThreshold:
    """Single-threshold grading mode."""

    @pytest.mark.unit
    def test_pass_when_meets_need(self) -> None:
        items = [
            GradedItem(item_id=str(i), group=None, correct=(i < 4)) for i in range(5)
        ]
        verdict = grade_diagnostic(graded_items=items, grading={"need": 4})
        assert verdict.correct == 4
        assert verdict.passed is True
        assert verdict.verdict == "win"

    @pytest.mark.unit
    def test_mid_when_half_correct_but_below_need(self) -> None:
        items = [
            GradedItem(item_id=str(i), group=None, correct=(i < 2)) for i in range(4)
        ]
        verdict = grade_diagnostic(graded_items=items, grading={"need": 3})
        assert verdict.passed is False
        assert verdict.verdict == "mid"

    @pytest.mark.unit
    def test_low_when_few_correct(self) -> None:
        items = [
            GradedItem(item_id=str(i), group=None, correct=(i < 1)) for i in range(5)
        ]
        verdict = grade_diagnostic(graded_items=items, grading={"need": 4})
        assert verdict.verdict == "low"

    @pytest.mark.unit
    def test_default_need_requires_all_correct(self) -> None:
        items = [GradedItem(item_id=str(i), group=None, correct=True) for i in range(3)]
        verdict = grade_diagnostic(graded_items=items, grading={})
        assert verdict.passed is True

    @pytest.mark.unit
    def test_string_need_is_coerced(self) -> None:
        items = [GradedItem(item_id=str(i), group=None, correct=True) for i in range(3)]
        verdict = grade_diagnostic(graded_items=items, grading={"need": "2"})
        assert verdict.passed is True

    @pytest.mark.unit
    def test_uncoercible_string_need_falls_back_to_total(self) -> None:
        items = [GradedItem(item_id=str(i), group=None, correct=True) for i in range(3)]
        # "lots" can't be parsed -> default == total == 3, all correct -> pass.
        verdict = grade_diagnostic(graded_items=items, grading={"need": "lots"})
        assert verdict.passed is True

    @pytest.mark.unit
    def test_bool_need_falls_back_to_total(self) -> None:
        items = [GradedItem(item_id=str(i), group=None, correct=True) for i in range(2)]
        # ``True`` is rejected (bool is not a valid threshold) -> default total.
        verdict = grade_diagnostic(graded_items=items, grading={"need": True})
        assert verdict.passed is True

    @pytest.mark.unit
    def test_empty_items(self) -> None:
        verdict = grade_diagnostic(graded_items=[], grading={"need": 0})
        assert verdict.total == 0
        assert verdict.verdict == "win"


class TestGradeDiagnosticFundPs:
    """Fundamentals / problem-solving two-threshold mode."""

    def _items(self, fund_correct: int, ps_correct: int) -> list[GradedItem]:
        fund = [
            GradedItem(item_id=f"f{i}", group="fund", correct=i < fund_correct)
            for i in range(3)
        ]
        ps = [
            GradedItem(item_id=f"p{i}", group="ps", correct=i < ps_correct)
            for i in range(3)
        ]
        return fund + ps

    @pytest.mark.unit
    def test_pass_requires_both_groups(self) -> None:
        grading = {"mode": "fundps", "fundNeeded": 2, "psNeeded": 2}
        verdict = grade_diagnostic(graded_items=self._items(2, 2), grading=grading)
        assert verdict.passed is True
        assert verdict.group_scores == {"fund": 2, "ps": 2}

    @pytest.mark.unit
    def test_fail_when_one_group_short(self) -> None:
        grading = {"mode": "fundps", "fundNeeded": 3, "psNeeded": 1}
        verdict = grade_diagnostic(graded_items=self._items(2, 3), grading=grading)
        assert verdict.passed is False
        assert verdict.group_scores["fund"] == 2

    @pytest.mark.unit
    def test_missing_thresholds_default_zero_passes(self) -> None:
        grading = {"mode": "fundps"}
        verdict = grade_diagnostic(graded_items=self._items(0, 0), grading=grading)
        # Needs default to 0, so zero-correct still passes.
        assert verdict.passed is True
