"""Diagnostic grading service.

Implements the auto-grader and instrument grading modes from the content
contract (``CONTENT_CONTRACT.md``) and the prototype's app logic. Symbolic
answers are *manual*: the runner self-marks them and submits a boolean, which the
server trusts for those items only.

Auto-graded items carry a numeric value ``v`` and/or a list of accepted string
forms ``accept``. An answer is correct when it parses to the same numeric value
as ``v`` (equivalent forms match: ``1/2`` == ``0.5`` == ``2^-1``) **or** its
normalised text equals a normalised entry in ``accept``. An item with neither a
``v`` nor a non-empty ``accept`` can never be auto-marked correct, matching the
contract.

Exact normalisation rules are finalised against ``CONSTANTS.md`` §8; the
implementation here strips surrounding whitespace, lower-cases, and removes
thousands separators and internal spaces before comparison.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction

GRADING_MODE_SINGLE = "single"
GRADING_MODE_FUNDPS = "fundps"

# Verdict labels (mirror the prototype / data model).
VERDICT_WIN = "win"
VERDICT_MID = "mid"
VERDICT_LOW = "low"

# Numeric tolerances (CONSTANTS.md §8): tight for integer-valued keys, relative
# otherwise.
_INTEGER_TOLERANCE = 1e-6
_RELATIVE_TOLERANCE = 1e-4
_MIN_RELATIVE_TOLERANCE = 0.01

_POWER_RE = re.compile(r"^\s*(-?\d+)\s*\^\s*(-?\d+)\s*$")
_MIXED_RE = re.compile(r"^\s*(-?\d+)\s+(\d+)\s*/\s*(\d+)\s*$")
_FRACTION_RE = re.compile(r"^\s*(-?\d+)\s*/\s*(\d+)\s*$")
_INT_RE = re.compile(r"^\s*(-?\d+)\s*$")


@dataclass(frozen=True)
class DiagnosticVerdict:
    """The graded outcome of a diagnostic attempt.

    Attributes:
        passed: Whether the instrument's threshold(s) were met.
        verdict: ``win`` | ``mid`` | ``low``.
        correct: Total correct item count (auto-graded plus self-marked).
        total: Total number of items considered.
        group_scores: Per-group correct counts (for ``fundps`` mode), else empty.
    """

    passed: bool
    verdict: str
    correct: int
    total: int
    group_scores: dict[str, int] = field(default_factory=dict)


def _parse_power(text: str) -> Fraction | None:
    """Parse an integer power like ``2^7`` or ``2^-1``.

    Args:
        text: The candidate text.

    Returns:
        The value, or ``None`` if not a power form or undefined (``0`` to a
        negative power).
    """
    match = _POWER_RE.match(text)
    if not match:
        return None
    base = int(match.group(1))
    exponent = int(match.group(2))
    if exponent >= 0:
        return Fraction(base**exponent, 1)
    if base == 0:
        return None  # 0 to a negative power is undefined
    return Fraction(1, base ** (-exponent))


def _parse_mixed(text: str) -> Fraction | None:
    """Parse a mixed number like ``1 3/4`` or ``-2 1/2``.

    Args:
        text: The candidate text.

    Returns:
        The value, or ``None`` if not a mixed-number form or the denominator is
        zero.
    """
    match = _MIXED_RE.match(text)
    if not match:
        return None
    whole = int(match.group(1))
    numerator = int(match.group(2))
    denominator = int(match.group(3))
    if denominator == 0:
        return None
    magnitude = abs(whole) + Fraction(numerator, denominator)
    return -magnitude if whole < 0 else magnitude


def _parse_fraction(text: str) -> Fraction | None:
    """Parse a simple fraction like ``5/7``.

    Args:
        text: The candidate text.

    Returns:
        The value, or ``None`` if not a fraction form or the denominator is zero.
    """
    match = _FRACTION_RE.match(text)
    if not match:
        return None
    denominator = int(match.group(2))
    if denominator == 0:
        return None
    return Fraction(int(match.group(1)), denominator)


def _parse_integer(text: str) -> Fraction | None:
    """Parse a signed integer.

    Args:
        text: The candidate text.

    Returns:
        The value, or ``None`` if not an integer form.
    """
    match = _INT_RE.match(text)
    if not match:
        return None
    return Fraction(int(match.group(1)), 1)


def _parse_decimal(text: str) -> Fraction | None:
    """Parse a decimal like ``0.75`` or ``-1.5`` via :class:`~fractions.Fraction`.

    Args:
        text: The candidate text.

    Returns:
        The value, or ``None`` if it is not a parseable number.
    """
    try:
        return Fraction(text)
    except (ValueError, ZeroDivisionError):
        return None


# Parsers tried in order; the first non-``None`` result wins.
_PARSERS = (_parse_power, _parse_mixed, _parse_fraction, _parse_integer, _parse_decimal)


def parse_numeric(raw: str) -> Fraction | None:
    """Parse a textual answer into an exact rational value.

    Recognises integers, fractions (``5/7``), mixed numbers (``1 3/4``), integer
    powers (``2^7``), and decimals (``0.5``). Returns ``None`` when the input is
    not a recognised numeric form (e.g. a symbolic expression), signalling that
    the item cannot be auto-graded by value.

    Args:
        raw: The raw answer text.

    Returns:
        The value as a :class:`~fractions.Fraction`, or ``None`` if unparseable.
    """
    text = raw.strip().replace(",", "")
    if not text:
        return None
    for parser in _PARSERS:
        value = parser(text)
        if value is not None:
            return value
    return None


# Leading variable/approximation prefixes stripped before string comparison
# (CONSTANTS.md §8): "x=", "r=", "≈", etc.
_PREFIX_RE = re.compile(r"^\s*(?:[a-z]\s*=|=|≈|~)\s*", re.IGNORECASE)
# Trailing alphabetic unit word stripped before string comparison, but only when
# a digit precedes it (so "96 miles" -> "96" while a word answer like "red" is
# left intact). The captured prefix ending in a digit is preserved.
_TRAILING_UNIT_RE = re.compile(r"^(.*\d)\s*[a-z]+\.?$", re.IGNORECASE)
# Unicode minus / dashes unified to ASCII hyphen-minus. The keys are
# intentionally the non-ASCII forms (U+2212 minus, en/em dashes), so the ruff
# ambiguous-character checks are suppressed here by design.
_MINUS_CHARS = str.maketrans({"−": "-", "–": "-", "—": "-"})  # noqa: RUF001


def _normalise_text(value: str) -> str:
    """Return a comparison-normalised form of a textual answer.

    Per CONSTANTS.md §8: trim, lower-case, unify minus signs, strip a leading
    ``x=`` / ``r=`` / ``≈`` style prefix, strip a trailing unit word *when it
    follows a number*, then remove commas and all remaining whitespace. So
    ``"x = 3,660"`` and ``"3660"`` compare equal, ``"96 miles"`` becomes ``"96"``,
    and a non-numeric answer such as ``"red"`` is preserved.

    Args:
        value: The raw text.

    Returns:
        The normalised comparison key.
    """
    text = value.strip().lower().translate(_MINUS_CHARS)
    text = _PREFIX_RE.sub("", text)
    unit_match = _TRAILING_UNIT_RE.match(text)
    if unit_match:
        text = unit_match.group(1)
    return re.sub(r"\s+", "", text.replace(",", ""))


def _numeric_tolerance(value: float) -> float:
    """Return the accept tolerance for a numeric key (CONSTANTS.md §8).

    Args:
        value: The item's canonical numeric value.

    Returns:
        ``1e-6`` when ``value`` is integer-valued, otherwise
        ``max(0.01, |value| * 1e-4)``.
    """
    if float(value).is_integer():
        return _INTEGER_TOLERANCE
    return max(_MIN_RELATIVE_TOLERANCE, abs(value) * _RELATIVE_TOLERANCE)


def check_auto(
    submitted: str,
    *,
    value: float | int | None,
    accept: list[str] | None = None,
) -> bool:
    """Return whether an auto-graded answer is correct (CONSTANTS.md §8).

    Accepts when either check passes:

    - **String match**: the normalised submission equals a normalised entry in
      ``accept``.
    - **Numeric match**: ``value`` is set and the submission parses to a number
      within tolerance of it (``1e-6`` for integer keys, otherwise
      ``max(0.01, |value| * 1e-4)``).

    An item with neither a ``value`` nor a non-empty ``accept`` can never be
    marked correct.

    Args:
        submitted: The user's raw answer.
        value: The item's canonical numeric value, or ``None`` if non-numeric.
        accept: Accepted string forms; compared after normalisation.

    Returns:
        True when the answer is accepted.
    """
    accept = accept or []
    if accept:
        submitted_norm = _normalise_text(submitted)
        if any(submitted_norm == _normalise_text(a) for a in accept):
            return True

    if value is not None:
        submitted_value = parse_numeric(submitted)
        if submitted_value is not None:
            difference = abs(float(submitted_value) - float(value))
            return difference <= _numeric_tolerance(value)

    return False


@dataclass(frozen=True)
class GradedItem:
    """A single graded diagnostic item.

    Attributes:
        item_id: The item's identifier.
        group: ``fund`` | ``ps`` | ``None``.
        correct: Whether the item was judged correct.
    """

    item_id: str
    group: str | None
    correct: bool


def _verdict_for(passed: bool, correct: int, total: int) -> str:
    """Return a three-way verdict label from a pass flag and score.

    "win" when passed; otherwise "mid" if at least half correct, else "low".

    Args:
        passed: Whether the instrument threshold was met.
        correct: Number of correct items.
        total: Total number of items.

    Returns:
        One of ``win`` | ``mid`` | ``low``.
    """
    if passed:
        return VERDICT_WIN
    if total > 0 and correct * 2 >= total:
        return VERDICT_MID
    return VERDICT_LOW


def grade_diagnostic(
    *,
    graded_items: list[GradedItem],
    grading: dict[str, object],
) -> DiagnosticVerdict:
    """Compute pass/verdict for a diagnostic attempt from graded items.

    Two grading modes are supported, selected by ``grading["mode"]``:

    - ``single``: pass when ``correct >= grading["need"]``.
    - ``fundps``: pass when fundamentals correct ``>= grading["fundNeeded"]`` and
      problem-solving correct ``>= grading["psNeeded"]``.

    An unknown or missing mode defaults to ``single`` with a ``need`` of the full
    item count (all correct required), matching the prototype's conservative
    fallback.

    Args:
        graded_items: Per-item correctness, including group labels.
        grading: The instrument's grading configuration.

    Returns:
        A :class:`DiagnosticVerdict`.
    """
    total = len(graded_items)
    correct = sum(1 for item in graded_items if item.correct)
    mode = grading.get("mode", GRADING_MODE_SINGLE)

    if mode == GRADING_MODE_FUNDPS:
        group_scores = {
            "fund": sum(1 for i in graded_items if i.group == "fund" and i.correct),
            "ps": sum(1 for i in graded_items if i.group == "ps" and i.correct),
        }
        fund_needed = _as_int(grading.get("fundNeeded"), default=0)
        ps_needed = _as_int(grading.get("psNeeded"), default=0)
        passed = group_scores["fund"] >= fund_needed and group_scores["ps"] >= ps_needed
        return DiagnosticVerdict(
            passed=passed,
            verdict=_verdict_for(passed, correct, total),
            correct=correct,
            total=total,
            group_scores=group_scores,
        )

    need = _as_int(grading.get("need"), default=total)
    passed = correct >= need
    return DiagnosticVerdict(
        passed=passed,
        verdict=_verdict_for(passed, correct, total),
        correct=correct,
        total=total,
    )


def _as_int(value: object, *, default: int) -> int:
    """Coerce a JSON-sourced grading threshold to ``int``.

    Args:
        value: The raw value from the grading config (may be ``None``, int, or a
            numeric string).
        default: Value to use when ``value`` is missing or not coercible.

    Returns:
        The integer threshold.
    """
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default
