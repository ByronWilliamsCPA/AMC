# Recommendation constants and placement logic

Everything the prototype uses to turn raw results into a course recommendation. All values are transcribed from the running app, not paraphrased. Where the app encodes logic in code, the algorithm is restated in plain terms with the exact thresholds.

The two content files referenced throughout are `amc_data.json` (the 9 AMC papers) and `diag_data.json` (the 10 diagnostics, the course ladder, and the catalog).

-----

## 1. AMC scoring

Two scoring modes, selected per test by the `scoreMode` field.

`count` (AMC 8): one point per correct answer, no penalty. A blank and a wrong answer are equal. Max equals the number of scored problems (25 unless some are voided).

`sixpoint` (AMC 10 and AMC 12): +6 per correct, +1.5 per blank, 0 per wrong. Max is `6 × scored problems` (150 for a full 25-problem paper). A blank is worth more than a wrong answer, which is the real contest incentive.

Voided problems (the `voided` array on a test, holding 1-based problem numbers) are excluded from correct/wrong/blank counts and removed from the max. None of the 9 bundled papers currently void anything; the mechanism exists because the 2025 AMC 12A (not bundled) had a defective problem 25.

Exact computation:

```
scored = N - count(voided)
count mode:    score = correct,                 max = scored
sixpoint mode: score = correct*6 + blank*1.5,   max = scored*6   (rounded to 0.1)
```

## 2. Performance bands

Advisory labels shown on a result screen, keyed off the final score. Cutoffs are inclusive at the lower bound (a score of exactly 60 is "Problem Series range").

AMC 8 (out of 25):

|Score|Label    |Meaning                         |
|-----|---------|--------------------------------|
|0–9  |Building |Fundamentals still forming      |
|10–14|Solid    |Comfortable on most of the paper|
|15–18|Strong   |Roughly Honor Roll territory    |
|19–25|Excellent|Distinguished Honor Roll range  |

AMC 10 and AMC 12 (out of 150):

|Score  |Label               |Meaning                                |
|-------|--------------------|---------------------------------------|
|0–44   |Foundation phase    |Below the contest problem-solving range|
|45–59  |Building phase      |Not yet at the Problem Series entry bar|
|60–79  |Problem Series range|At or above the 60 entry bar           |
|80–99  |Final Fives range   |Eligible for AMC 10 Final Fives        |
|100–119|AIME-track          |AMC 12 at 100+ is near AIME-qualifying |
|120–150|Advanced            |AIME-level                             |

AMC 8 cutoffs are percentile-based on the real contest and shift year to year, so the Honor Roll labels are approximate. The AMC 10/12 bands encode the AoPS course gates in section 3.

## 3. AMC 10 score gates

From the AoPS course pages. These drive which contest courses a score unlocks. They are stored in the diagnostic catalog (`gate: "amc"`, `min`) and restated in the bands.

|AMC 10 score|Unlocks                                                                           |
|------------|----------------------------------------------------------------------------------|
|< 60        |Finish the Introduction series first (Algebra B, Counting, Number Theory)         |
|60+         |AMC 10 Problem Series (also requires a completed algebra course)                  |
|80+         |AMC 10 Final Fives (problems 21–25)                                               |
|100+        |AoPS suggests AIME Problem Series, Intro Geometry, or Intermediate Algebra instead|

The 60+ gate is a conjunction: the score alone does not unlock the Problem Series without a completed algebra course. The combined view flags this tension when a student's AMC score clears 60 but the diagnostics show algebra is unfinished.

## 4. Course ladder and catalog

The ladder (the algebra spine the placement engine walks, in order) lives at `diag.ladder`:

1. Prealgebra 1
1. Prealgebra 2
1. Intro to Algebra A
1. Intro to Algebra B

The catalog (`diag.catalog`) is the fuller course list shown on the Plan tab, each tagged by how placement is decided:

|# |Course                         |Placed by   |Note                                                                    |
|--|-------------------------------|------------|------------------------------------------------------------------------|
|1 |Prealgebra 1                   |diagnostic  |Arithmetic, fractions, decimals, ratios                                 |
|2 |Prealgebra 2                   |diagnostic  |Exponents, number theory, roots, basic geometry, stats, intro counting  |
|3 |Intro to Algebra A             |diagnostic  |Variables, linear equations, exponents, ratios                          |
|4 |Intro to Algebra B             |diagnostic  |Quadratics, functions, polynomials, complex numbers; prereq for Geometry|
|5 |Intro to Counting & Probability|diagnostic  |Combinatorics foundations; same level as Intro Number Theory            |
|6 |Intro to Number Theory         |prerequisite|Prereq: Intro to Algebra A. No diagnostic                               |
|7 |Intro to Geometry              |prerequisite|Prereq: Intro to Algebra B. No diagnostic                               |
|8 |AMC 10 Problem Series          |AMC 60+     |Plus a completed algebra course                                         |
|9 |AMC 10 Final Fives             |AMC 80+     |Targets problems 21–25                                                  |
|10|Intermediate Algebra           |prerequisite|Typically follows Intro to Geometry. No diagnostic                      |

Only the five `diagnostic` courses have built-in instruments. The rest are placed by prerequisite or AMC score and carry no diagnostic.

## 5. Diagnostic instruments and pass thresholds

Ten instruments, one readiness check ("Are You Ready?", role `AYR`) and one mastery check ("Do You Know?", role `DYK`) per diagnostic course. Two grading modes:

`single`: count correct across all items; pass if `correct >= need`.

`fundps`: items are split into a Fundamentals group and a Problem Solving group (the `group` field on each item, `"fund"` or `"ps"`); pass requires clearing both bars, `fund >= fundNeeded` AND `ps >= psNeeded`.

|Instrument|Role|Mode  |Thresholds                             |
|----------|----|------|---------------------------------------|
|pa1-pre   |AYR |single|23 of 28                               |
|pa1-post  |DYK |fundps|fund 23/25, ps 4/8                     |
|pa2-pre   |AYR |fundps|fund 23/25, ps 4/8                     |
|pa2-post  |DYK |fundps|fund 20/22, ps 3/6                     |
|algA-pre  |AYR |fundps|fund 19/23, ps 3/6 (special, see below)|
|algA-post |DYK |fundps|fund 11/12, ps 4/7                     |
|algB-pre  |AYR |fundps|fund 11/12, ps 4/7                     |
|algB-post |DYK |single|7 of 9                                 |
|count-pre |AYR |single|7 of 9                                 |
|count-post|DYK |single|9 of 11                                |

A post-test and the next course's pre-test are the same instrument by design (for example pa1-post equals pa2-pre, algA-post equals algB-pre). They share thresholds, which is why the rows above match in pairs.

The `algA-pre` special case (`special: "algA_ayr"`): readiness is judged in three tiers rather than a flat pass. Under 80% of Fundamentals (`fund < ceil(0.8 * fundTotal)`) sends the student down to Prealgebra 2 (or Prealgebra 1 if needed). Fundamentals at or above 80% but Problem Solving under its bar recommends Prealgebra 2 to build problem-solving maturity. Both clear means ready for Intro to Algebra A.

## 6. Per-instrument recommendation

Run after grading a single instrument. `L` is that instrument's `ladder` object (`prev`, `self`, `next`).

For an AYR (readiness) instrument: pass means "ready for `self`, next run its DYK check"; fail means "not ready for `self`, drop to `prev`." The algA-pre special case overrides this with the three-tier logic above.

For a DYK (mastery) instrument: pass means "`self` would be mostly review, move up to `next`"; fail means "`self` is the right level to start."

This is the rule stated on the Plan tab: the right starting class is the first course where the student passes the readiness check but not the mastery check.

## 7. Combined placement (the synthesize step)

Walks the four-course ladder in order, using the latest stored result per course and role, and picks a single starting class:

1. For each course top to bottom: if its DYK was passed, treat the course as mastered and continue climbing.
1. If its AYR was taken and failed, start at the previous course (reason: failed the readiness check). Stop.
1. If its AYR passed, or its DYK was taken and failed, start at this course. Stop. (If the DYK was the signal, the reason notes "ready but didn't pass mastery.")
1. If there is no data for the course, keep looking.

If the walk falls off the end (all four mastered), the recommendation is "Intro to Geometry / Intro Number Theory, foundation done." With no diagnostic data at all, there is no recommendation.

The combined view then layers the AMC 10 score on top: it lists the courses the latest AMC 10 unlocks (the section 3 gates) and, if the AMC score clears 60 while the algebra ladder is unfinished, shows the conjunction warning.

## 8. Auto-grading of typed answers

Diagnostic items are free-response. Non-manual items (`manual: false`) are graded automatically; manual items (`manual: true`, the symbolic answers like radicals and ordered pairs) are self-marked by the student against a revealed key and contribute to the same pass counts.

Auto-grading accepts an answer if either check passes:

String match: normalize the input (trim, lowercase, unify minus signs, strip commas/spaces, strip a leading `x=`/`r=`/`≈` style prefix, strip a trailing unit word) and compare against each entry in the item's `accept` list, normalized the same way.

Numeric match: if the item has a numeric value `v`, parse the input as a number (supporting integers, decimals, fractions like `5/7`, mixed numbers like `2 3/4`, and simple powers like `2^5`) and accept if it is within tolerance. Tolerance is `1e-6` for integer `v`, otherwise `max(0.01, |v| * 1e-4)`.

An item with no `accept` matches and no `v` can only be graded by the string list, so any item meant for auto-grading needs at least one of `accept` or `v`.
