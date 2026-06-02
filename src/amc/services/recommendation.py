"""Placement recommendation service (``synthesize``).

Implements the combined-placement algorithm transcribed in ``CONSTANTS.md`` §7,
plus the per-instrument rule (§6), the ``algA_ayr`` three-tier special case (§5),
and the AMC-10 score gates (§3). All thresholds come from the seeded content
(instrument ``grading`` and the diagnostic ``catalog``); nothing is hard-coded
here, so re-seeding new content changes behaviour without code edits.

The service walks the four-course algebra ladder (``diag.ladder``) using the
latest stored result per course and role:

1. If a course's DYK (mastery) check passed, treat it as mastered and climb.
2. If its AYR (readiness) check was taken and failed, start at the previous
   course and stop.
3. If its AYR passed, or its DYK was taken and failed, start at this course and
   stop (noting "ready but didn't pass mastery" when the DYK drove it).
4. With no data for a course, keep looking.

If the walk clears all four, the recommendation is the "foundation done" course
that the top instrument's ladder names as ``next``. With no diagnostic data at
all there is no recommendation. The AMC-10 score is then layered on top as an
advisory list of unlocked courses plus the 60+/unfinished-algebra conjunction
warning.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Roles, mirrored from the content model.
ROLE_AYR = "AYR"
ROLE_DYK = "DYK"

# Fundamentals fraction required by the algA-pre special case (CONSTANTS.md §5).
_ALGA_FUND_FRACTION = 0.8

# AMC-10 conjunction warning fires at this score while algebra is unfinished.
_AMC10_ALGEBRA_GATE = 60.0


@dataclass(frozen=True)
class InstrumentResult:
    """The latest stored outcome for one instrument.

    Attributes:
        instrument_id: The instrument slug (e.g. ``algA-pre``).
        course: The course the instrument assesses.
        role: ``AYR`` or ``DYK``.
        passed: Whether the instrument's threshold(s) were met.
        ladder: ``prev`` / ``self`` / ``next`` course labels.
        fund_correct: Fundamentals-group correct count (``fundps`` only).
        fund_total: Fundamentals-group item count (``fundps`` only).
        ps_correct: Problem-solving-group correct count (``fundps`` only).
        ps_needed: Problem-solving pass threshold (``fundps`` only).
        special: Optional special-case tag (e.g. ``algA_ayr``).
    """

    instrument_id: str
    course: str
    role: str
    passed: bool
    ladder: dict[str, str]
    fund_correct: int = 0
    fund_total: int = 0
    ps_correct: int = 0
    ps_needed: int = 0
    special: str | None = None


@dataclass(frozen=True)
class AmcGate:
    """A score gate from the diagnostic catalog (``gate: "amc"``).

    Attributes:
        course: The course the gate unlocks.
        min_score: Inclusive AMC-10 score at or above which it unlocks.
        note: Advisory text shown alongside the unlocked course.
    """

    course: str
    min_score: float
    note: str = ""


@dataclass(frozen=True)
class Recommendation:
    """The synthesized placement recommendation.

    Attributes:
        course: Recommended starting course, or ``None`` if undetermined.
        reason: Human-readable explanation of why.
        unlocked_by_amc: Courses the latest AMC-10 score unlocks (advisory).
        algebra_warning: Conjunction warning when AMC clears 60 but the algebra
            ladder is unfinished, else ``None``.
    """

    course: str | None
    reason: str
    unlocked_by_amc: list[str] = field(default_factory=list)
    algebra_warning: str | None = None


def recommend_for_instrument(result: InstrumentResult) -> str:
    """Return the per-instrument recommendation course (CONSTANTS.md §6).

    Applies the ``algA_ayr`` three-tier special case when tagged; otherwise the
    standard AYR/DYK rule.

    Args:
        result: The graded instrument outcome.

    Returns:
        The course label the single instrument points to.
    """
    ladder = result.ladder
    if result.special == "algA_ayr" and result.role == ROLE_AYR:
        return _alga_ayr_target(result)

    if result.role == ROLE_AYR:
        # Readiness: pass -> ready for self; fail -> drop to prev.
        if result.passed:
            return ladder.get("self", result.course)
        return ladder.get("prev", result.course)

    # Mastery (DYK): pass -> move up to next; fail -> start at self.
    if result.passed:
        return ladder.get("next", result.course)
    return ladder.get("self", result.course)


def _alga_ayr_target(result: InstrumentResult) -> str:
    """Return the course for the algA-pre three-tier readiness check.

    Under 80% of Fundamentals drops to ``prev``; Fundamentals fine but Problem
    Solving under its bar holds at ``prev`` to build problem-solving maturity;
    both clear means ready for ``self`` (CONSTANTS.md §5).

    Args:
        result: The algA-pre AYR outcome.

    Returns:
        The recommended course label.
    """
    ladder = result.ladder
    fund_bar = _ceil_fraction(result.fund_total, _ALGA_FUND_FRACTION)
    if result.fund_correct < fund_bar:
        return ladder.get("prev", result.course)
    if result.ps_correct < result.ps_needed:
        # Fundamentals fine, problem-solving weak: build maturity at prev.
        return ladder.get("prev", result.course)
    return ladder.get("self", result.course)


def _ceil_fraction(total: int, fraction: float) -> int:
    """Return ``ceil(total * fraction)`` using integer math.

    Args:
        total: The item count.
        fraction: The required fraction (e.g. 0.8).

    Returns:
        The smallest integer at or above ``total * fraction``.
    """
    # Scale to avoid floating-point edge cases at exact boundaries.
    scaled = total * fraction
    whole = int(scaled)
    return whole if whole == scaled else whole + 1


def synthesize(
    *,
    ladder: list[str],
    results: dict[str, InstrumentResult],
    amc10_score: float | None = None,
    amc_gates: list[AmcGate] | None = None,
) -> Recommendation:
    """Combine diagnostic results and an AMC-10 score into a recommendation.

    Implements the ladder walk of CONSTANTS.md §7. ``results`` maps a course name
    to that course's most relevant latest result; the walk consults the AYR and
    DYK signals per course in ladder order.

    Args:
        ladder: Ordered course names (``diag.ladder``).
        results: Latest instrument result keyed by ``f"{course}:{role}"`` so both
            the readiness and mastery signals for a course are available.
        amc10_score: The student's latest AMC-10 score, if any.
        amc_gates: Catalog AMC gates; used for the advisory unlock list.

    Returns:
        A :class:`Recommendation`.
    """
    amc_gates = amc_gates or []
    has_any = bool(results)

    chosen: str | None = None
    reason = ""
    mastered_all = True

    for course in ladder:
        ayr = results.get(f"{course}:{ROLE_AYR}")
        dyk = results.get(f"{course}:{ROLE_DYK}")

        if dyk is not None and dyk.passed:
            # Mastered this course; keep climbing.
            continue

        if ayr is not None and not ayr.passed:
            chosen = recommend_for_instrument(ayr)
            reason = f"Failed the {course} readiness check; start at {chosen}."
            mastered_all = False
            break

        if ayr is not None and ayr.passed:
            chosen = ayr.ladder.get("self", course)
            reason = f"Passed the {course} readiness check; start at {chosen}."
            mastered_all = False
            break

        if dyk is not None and not dyk.passed:
            chosen = dyk.ladder.get("self", course)
            reason = (
                f"Ready for {course} but didn't pass its mastery check; "
                f"start at {chosen}."
            )
            mastered_all = False
            break

        # No data for this course: keep looking.
        mastered_all = False

    if chosen is None and has_any and mastered_all:
        # Fell off the end: every ladder course mastered.
        top = ladder[-1]
        top_dyk = results.get(f"{top}:{ROLE_DYK}")
        nxt = top_dyk.ladder.get("next", top) if top_dyk else top
        chosen = nxt
        reason = f"All ladder courses mastered; move on to {nxt}."

    unlocked, warning = _apply_amc(amc10_score, amc_gates, mastered_all, has_any)

    if chosen is None and not has_any:
        no_data_reason = (
            "No diagnostics taken yet; take a placement check to get a recommendation."
        )
        return Recommendation(
            course=None,
            reason=no_data_reason,
            unlocked_by_amc=unlocked,
            algebra_warning=warning,
        )

    return Recommendation(
        course=chosen,
        reason=reason,
        unlocked_by_amc=unlocked,
        algebra_warning=warning,
    )


def _apply_amc(
    amc10_score: float | None,
    amc_gates: list[AmcGate],
    mastered_all: bool,
    has_any: bool,
) -> tuple[list[str], str | None]:
    """Return the AMC-unlocked course list and any conjunction warning.

    Args:
        amc10_score: Latest AMC-10 score, if any.
        amc_gates: Catalog AMC gates.
        mastered_all: Whether every ladder course is mastered.
        has_any: Whether any diagnostic data exists.

    Returns:
        A tuple of (unlocked course names, optional warning message).
    """
    if amc10_score is None:
        return [], None

    unlocked = [g.course for g in amc_gates if amc10_score >= g.min_score]

    warning: str | None = None
    algebra_unfinished = has_any and not mastered_all
    if amc10_score >= _AMC10_ALGEBRA_GATE and algebra_unfinished:
        warning = (
            f"AMC 10 score {amc10_score:g} clears the 60+ Problem Series bar, but "
            "the algebra ladder is unfinished. Finish the algebra track before "
            "relying on the Problem Series."
        )
    return unlocked, warning
