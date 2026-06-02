"""Unit tests for the exam grading service.

Covers both scoring modes, voided handling, blanks, answer normalisation, the
short-``answers`` case, and every validation guard. Targets 100% coverage of
``amc.services.grading`` per the tech-spec requirement for the grading service.
"""

import pytest

from amc.core.exceptions import ValidationError
from amc.services.grading import (
    SCORE_MODE_COUNT,
    SCORE_MODE_SIXPOINT,
    score_exam,
)


class TestScoreExamSixPoint:
    """Six-point mode (AMC 10/12)."""

    @pytest.mark.unit
    def test_all_correct(self) -> None:
        key = ["A", "B", "C", "D", "E"]
        result = score_exam(answer_key=key, answers=key, score_mode=SCORE_MODE_SIXPOINT)
        assert result.correct == 5
        assert result.wrong == 0
        assert result.blank == 0
        assert result.score == 30.0  # 5 * 6
        assert result.max_score == 30.0

    @pytest.mark.unit
    def test_blanks_award_partial(self) -> None:
        key = ["A", "B", "C", "D"]
        answers = ["A", None, None, "D"]
        result = score_exam(
            answer_key=key, answers=answers, score_mode=SCORE_MODE_SIXPOINT
        )
        assert result.correct == 2
        assert result.blank == 2
        assert result.wrong == 0
        assert result.score == 2 * 6 + 2 * 1.5  # 15.0
        assert result.max_score == 24.0

    @pytest.mark.unit
    def test_wrong_answers_score_zero_each(self) -> None:
        key = ["A", "B", "C"]
        answers = ["B", "A", "C"]
        result = score_exam(
            answer_key=key, answers=answers, score_mode=SCORE_MODE_SIXPOINT
        )
        assert result.correct == 1
        assert result.wrong == 2
        assert result.score == 6.0


class TestScoreExamCount:
    """Count mode (AMC 8)."""

    @pytest.mark.unit
    def test_score_equals_correct(self) -> None:
        key = ["A", "B", "C", "D", "E"]
        answers = ["A", "B", "X", None, "E"]
        result = score_exam(
            answer_key=key, answers=answers, score_mode=SCORE_MODE_COUNT
        )
        assert result.correct == 3
        assert result.wrong == 1
        assert result.blank == 1
        assert result.score == 3.0
        assert result.max_score == 5.0


class TestVoided:
    """Voided problems are excluded from all counts and the maximum."""

    @pytest.mark.unit
    def test_voided_excluded_from_scoring(self) -> None:
        key = ["A", "B", "C", "D", "E"]
        answers = ["A", "B", "C", "D", "E"]
        result = score_exam(
            answer_key=key,
            answers=answers,
            score_mode=SCORE_MODE_SIXPOINT,
            voided=[3],
        )
        # Problem 3 voided: 4 scored problems, all correct.
        assert result.correct == 4
        assert result.max_score == 24.0
        assert result.score == 24.0
        void_item = next(item for item in result.review if item.n == 3)
        assert void_item.voided is True
        assert void_item.ok is False

    @pytest.mark.unit
    def test_out_of_range_voided_ignored(self) -> None:
        key = ["A", "B"]
        result = score_exam(
            answer_key=key,
            answers=key,
            score_mode=SCORE_MODE_COUNT,
            voided=[0, 99],
        )
        assert result.correct == 2
        assert result.max_score == 2.0


class TestNormalisation:
    """Whitespace and case are normalised before comparison."""

    @pytest.mark.unit
    def test_case_and_whitespace_insensitive(self) -> None:
        result = score_exam(
            answer_key=["A", "B"],
            answers=[" a ", "b"],
            score_mode=SCORE_MODE_COUNT,
        )
        assert result.correct == 2

    @pytest.mark.unit
    def test_empty_string_is_blank(self) -> None:
        result = score_exam(
            answer_key=["A", "B"],
            answers=["", "B"],
            score_mode=SCORE_MODE_SIXPOINT,
        )
        assert result.blank == 1
        assert result.correct == 1


class TestShortAnswers:
    """``answers`` shorter than the key treats missing entries as blanks."""

    @pytest.mark.unit
    def test_missing_trailing_answers_are_blank(self) -> None:
        result = score_exam(
            answer_key=["A", "B", "C"],
            answers=["A"],
            score_mode=SCORE_MODE_SIXPOINT,
        )
        assert result.correct == 1
        assert result.blank == 2
        assert len(result.review) == 3


class TestValidation:
    """Guard clauses raise ValidationError."""

    @pytest.mark.unit
    def test_unknown_score_mode(self) -> None:
        with pytest.raises(ValidationError):
            score_exam(answer_key=["A"], answers=["A"], score_mode="bogus")

    @pytest.mark.unit
    def test_empty_answer_key(self) -> None:
        with pytest.raises(ValidationError):
            score_exam(answer_key=[], answers=[], score_mode=SCORE_MODE_COUNT)

    @pytest.mark.unit
    def test_too_many_answers(self) -> None:
        with pytest.raises(ValidationError):
            score_exam(
                answer_key=["A"],
                answers=["A", "B"],
                score_mode=SCORE_MODE_COUNT,
            )
