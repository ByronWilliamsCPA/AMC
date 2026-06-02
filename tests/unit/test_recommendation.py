"""Unit tests for the placement recommendation service.

Exercises the combined ladder walk (CONSTANTS.md §7), the per-instrument rule
(§6), the ``algA_ayr`` three-tier special case (§5), and the AMC-10 gate/warning
layering (§3). Targets 100% coverage of ``amc.services.recommendation``.
"""

import pytest

from amc.services.recommendation import (
    AmcGate,
    InstrumentResult,
    Recommendation,
    recommend_for_instrument,
    synthesize,
)

LADDER = [
    "Prealgebra 1",
    "Prealgebra 2",
    "Intro to Algebra A",
    "Intro to Algebra B",
]

_LADDERS = {
    "Prealgebra 1": {
        "prev": "foundational arithmetic review",
        "self": "Prealgebra 1",
        "next": "Prealgebra 2",
    },
    "Prealgebra 2": {
        "prev": "Prealgebra 1",
        "self": "Prealgebra 2",
        "next": "Intro to Algebra A",
    },
    "Intro to Algebra A": {
        "prev": "Prealgebra 2",
        "self": "Intro to Algebra A",
        "next": "Intro to Algebra B",
    },
    "Intro to Algebra B": {
        "prev": "Intro to Algebra A",
        "self": "Intro to Algebra B",
        "next": "Intro to Geometry / Intro Number Theory",
    },
}


def _result(course: str, role: str, *, passed: bool, **kw: object) -> InstrumentResult:
    return InstrumentResult(
        instrument_id=f"{course}:{role}",
        course=course,
        role=role,
        passed=passed,
        ladder=_LADDERS[course],
        **kw,  # type: ignore[arg-type]
    )


class TestPerInstrument:
    """The single-instrument rule (CONSTANTS.md §6)."""

    @pytest.mark.unit
    def test_ayr_pass_targets_self(self) -> None:
        r = _result("Prealgebra 2", "AYR", passed=True)
        assert recommend_for_instrument(r) == "Prealgebra 2"

    @pytest.mark.unit
    def test_ayr_fail_drops_to_prev(self) -> None:
        r = _result("Prealgebra 2", "AYR", passed=False)
        assert recommend_for_instrument(r) == "Prealgebra 1"

    @pytest.mark.unit
    def test_dyk_pass_moves_up_to_next(self) -> None:
        r = _result("Prealgebra 2", "DYK", passed=True)
        assert recommend_for_instrument(r) == "Intro to Algebra A"

    @pytest.mark.unit
    def test_dyk_fail_holds_at_self(self) -> None:
        r = _result("Prealgebra 2", "DYK", passed=False)
        assert recommend_for_instrument(r) == "Prealgebra 2"


class TestAlgASpecial:
    """The algA-pre three-tier readiness logic (CONSTANTS.md §5)."""

    @pytest.mark.unit
    def test_low_fundamentals_drops_to_prev(self) -> None:
        # fund 17/23 -> below ceil(0.8*23)=19 -> drop to Prealgebra 2.
        r = _result(
            "Intro to Algebra A",
            "AYR",
            passed=False,
            fund_correct=17,
            fund_total=23,
            ps_correct=5,
            ps_needed=3,
            special="algA_ayr",
        )
        assert recommend_for_instrument(r) == "Prealgebra 2"

    @pytest.mark.unit
    def test_fundamentals_ok_problem_solving_weak_holds_prev(self) -> None:
        # fund 20/23 (>=19) but ps 1/? below need -> Prealgebra 2.
        r = _result(
            "Intro to Algebra A",
            "AYR",
            passed=False,
            fund_correct=20,
            fund_total=23,
            ps_correct=1,
            ps_needed=3,
            special="algA_ayr",
        )
        assert recommend_for_instrument(r) == "Prealgebra 2"

    @pytest.mark.unit
    def test_both_clear_ready_for_self(self) -> None:
        r = _result(
            "Intro to Algebra A",
            "AYR",
            passed=True,
            fund_correct=21,
            fund_total=23,
            ps_correct=5,
            ps_needed=3,
            special="algA_ayr",
        )
        assert recommend_for_instrument(r) == "Intro to Algebra A"

    @pytest.mark.unit
    def test_fund_bar_exact_boundary_passes(self) -> None:
        # ceil(0.8*25) = 20; exactly 20 should clear the fundamentals bar.
        r = _result(
            "Intro to Algebra A",
            "AYR",
            passed=True,
            fund_correct=20,
            fund_total=25,
            ps_correct=5,
            ps_needed=3,
            special="algA_ayr",
        )
        assert recommend_for_instrument(r) == "Intro to Algebra A"


class TestSynthesizeWalk:
    """The combined ladder walk (CONSTANTS.md §7)."""

    @pytest.mark.unit
    def test_no_data_no_recommendation(self) -> None:
        rec = synthesize(ladder=LADDER, results={})
        assert rec.course is None
        assert "No diagnostics" in rec.reason

    @pytest.mark.unit
    def test_first_failed_readiness_stops_walk(self) -> None:
        results = {
            "Prealgebra 1:DYK": _result("Prealgebra 1", "DYK", passed=True),
            "Prealgebra 2:AYR": _result("Prealgebra 2", "AYR", passed=False),
        }
        rec = synthesize(ladder=LADDER, results=results)
        # Prealgebra 1 mastered, Prealgebra 2 readiness failed -> start prev.
        assert rec.course == "Prealgebra 1"
        assert "readiness" in rec.reason

    @pytest.mark.unit
    def test_passed_readiness_starts_at_self(self) -> None:
        results = {
            "Intro to Algebra A:AYR": _result("Intro to Algebra A", "AYR", passed=True),
        }
        rec = synthesize(ladder=LADDER, results=results)
        assert rec.course == "Intro to Algebra A"

    @pytest.mark.unit
    def test_ready_but_failed_mastery(self) -> None:
        results = {
            "Prealgebra 1:DYK": _result("Prealgebra 1", "DYK", passed=False),
        }
        rec = synthesize(ladder=LADDER, results=results)
        assert rec.course == "Prealgebra 1"
        assert "mastery" in rec.reason

    @pytest.mark.unit
    def test_all_mastered_moves_off_ladder(self) -> None:
        results = {
            f"{course}:DYK": _result(course, "DYK", passed=True) for course in LADDER
        }
        rec = synthesize(ladder=LADDER, results=results)
        assert rec.course == "Intro to Geometry / Intro Number Theory"
        assert "mastered" in rec.reason


class TestSynthesizeAmc:
    """AMC-10 gate and conjunction-warning layering (CONSTANTS.md §3)."""

    @pytest.mark.unit
    def _gates(self) -> list[AmcGate]:
        return [
            AmcGate(course="AMC 10 Problem Series", min_score=60),
            AmcGate(course="AMC 10 Final Fives", min_score=80),
        ]

    @pytest.mark.unit
    def test_unlocked_list_reflects_score(self) -> None:
        rec = synthesize(
            ladder=LADDER,
            results={},
            amc10_score=85,
            amc_gates=self._gates(),
        )
        assert rec.unlocked_by_amc == ["AMC 10 Problem Series", "AMC 10 Final Fives"]

    @pytest.mark.unit
    def test_no_score_no_unlocks(self) -> None:
        rec = synthesize(ladder=LADDER, results={}, amc_gates=self._gates())
        assert rec.unlocked_by_amc == []
        assert rec.algebra_warning is None

    @pytest.mark.unit
    def test_conjunction_warning_when_algebra_unfinished(self) -> None:
        results = {
            "Prealgebra 2:AYR": _result("Prealgebra 2", "AYR", passed=False),
        }
        rec = synthesize(
            ladder=LADDER,
            results=results,
            amc10_score=72,
            amc_gates=self._gates(),
        )
        assert rec.algebra_warning is not None
        assert "unfinished" in rec.algebra_warning

    @pytest.mark.unit
    def test_no_warning_when_all_mastered(self) -> None:
        results = {
            f"{course}:DYK": _result(course, "DYK", passed=True) for course in LADDER
        }
        rec = synthesize(
            ladder=LADDER,
            results=results,
            amc10_score=72,
            amc_gates=self._gates(),
        )
        assert rec.algebra_warning is None


class TestRecommendationDataclass:
    """The result container."""

    @pytest.mark.unit
    def test_defaults(self) -> None:
        rec = Recommendation(course="X", reason="because")
        assert rec.unlocked_by_amc == []
        assert rec.algebra_warning is None
