# Content contract

The exact shape of the two data files the prototype consumes. The seed script validates against this; anything conforming drops in without touching app code.

Both files are JSON, UTF-8. Images are inlined as `data:` URIs (no external files), which is why the bundle runs offline. Math is LaTeX written with `\( ... \)` inline delimiters and rendered by the embedded KaTeX at runtime.

Current payload: 9 AMC papers (3 each at AMC 8 / 10 / 12), 225 problems total (75 image-mode, 150 LaTeX-mode), and 10 diagnostic instruments holding 218 items (45 of them self-marked).

-----

## File 1: `amc_data.json`

Top level:

```json
{
  "tests":   { "<testId>": <Test>, ... },
  "byContest": { "AMC 8": ["<testId>", ...], "AMC 10": [...], "AMC 12": [...] },
  "keyedTests": ["2017A", "2018A", ...]
}
```

`byContest` is the display grouping and order on the Tests tab. Every id listed must exist in `tests`. The three keys are exactly `"AMC 8"`, `"AMC 10"`, `"AMC 12"`.

`keyedTests` is an informational list of AMC 10 papers for which an answer key is on file (not all are bundled as full tests). The app shows its length as a count. It does not gate anything; it can be an empty array without breaking the app.

### Test object

```json
{
  "id":          "AMC12-2022A",
  "contest":     "AMC 12",
  "year":        2022,
  "exam":        "A",
  "durationSec": 4500,
  "scoreMode":   "sixpoint",
  "mode":        "latex",
  "voided":      [25],
  "answers":     ["D","E","B", ...],
  "problems":    [ <Problem>, ... ]
}
```

|Field        |Type     |Rule                                                                                                                                                     |
|-------------|---------|---------------------------------------------------------------------------------------------------------------------------------------------------------|
|`id`         |string   |Unique across `tests`. Convention `AMC<level>-<year><exam>`, e.g. `AMC8-2019`, `AMC10-2017A`. Used as the localStorage attempt key, so it must be stable.|
|`contest`    |string   |One of `AMC 8`, `AMC 10`, `AMC 12`. Selects the band table.                                                                                              |
|`year`       |number   |Display only.                                                                                                                                            |
|`exam`       |string   |`A`, `B`, or `""` (AMC 8 has no variant). Display only.                                                                                                  |
|`durationSec`|number   |Timer length. 2400 for AMC 8, 4500 for AMC 10/12.                                                                                                        |
|`scoreMode`  |string   |`count` (AMC 8) or `sixpoint` (AMC 10/12). See CONSTANTS §1.                                                                                             |
|`mode`       |string   |`img` or `latex`. Determines how a problem renders; must match the problem objects (see below).                                                          |
|`voided`     |number[] |Optional. 1-based problem numbers excluded from scoring. Omit or `[]` for none.                                                                          |
|`answers`    |string[] |Length must equal `problems.length` (25). Each entry `A`–`E`, or `null` for a voided problem with no correct choice. Index i is the key for problem i+1. |
|`problems`   |Problem[]|Exactly 25, in order.                                                                                                                                    |

### Problem object, image mode (`mode: "img"`)

Used by the bundled AMC 10 papers (official problem scans).

```json
{ "n": 1, "img": "data:image/png;base64,iVBOR...", "sol": "https://artofproblemsolving.com/wiki/...Problem_1" }
```

|Field|Type  |Rule                                                                                                                               |
|-----|------|-----------------------------------------------------------------------------------------------------------------------------------|
|`n`  |number|1-based problem number.                                                                                                            |
|`img`|string|`data:image/png;base64,...` or jpeg. The whole problem including its choices is in the image; the app shows A–E buttons separately.|
|`sol`|string|Link out to the solution. Never embed solution text.                                                                               |

### Problem object, LaTeX mode (`mode: "latex"`)

Used by the bundled AMC 8 and AMC 12 papers.

```json
{
  "n": 1,
  "q": "What is the value of \\( 3 + \\frac{1}{3} \\)? <img src=\"data:image/svg+xml;base64,...\">",
  "choices": [ {"L":"A","html":"\\(6\\)"}, {"L":"B","html":"\\(8\\)"}, ... ],
  "sol": "https://artofproblemsolving.com/wiki/...Problem_1"
}
```

|Field    |Type  |Rule                                                                                                                                                             |
|---------|------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
|`n`      |number|1-based.                                                                                                                                                         |
|`q`      |string|Problem statement as HTML. Math in `\( ... \)`. Any diagram is an inline `<img>` with a `data:` URI (SVG for AMC 8, PNG/JPEG for AMC 12). No external image URLs.|
|`choices`|array |Exactly 5. Each `{ "L": "A".."E", "html": "<choice as HTML/LaTeX>" }`. `html` must be non-empty.                                                                 |
|`sol`    |string|Link out.                                                                                                                                                        |

A LaTeX-mode test must have every problem in LaTeX form; an image-mode test, every problem in image form. The app branches on the test-level `mode`, so the two shapes are not mixed within one test.

## File 2: `diag_data.json`

Top level:

```json
{
  "instruments": { "<instrumentId>": <Instrument>, ... },
  "order":       ["pa1-pre", "pa1-post", ...],
  "ladder":      ["Prealgebra 1", "Prealgebra 2", "Intro to Algebra A", "Intro to Algebra B"],
  "catalog":     [ <CatalogRow>, ... ]
}
```

`order` is the display order on the Diagnostics tab; every id must exist in `instruments`. `ladder` and `catalog` are documented in CONSTANTS §4 and feed the placement engine and Plan tab. The four ladder strings must match the `course` values of the corresponding instruments and the `course` entries in the catalog exactly, since the synthesize step joins on that string.

### Instrument object

```json
{
  "id":           "pa1-pre",
  "course":       "Prealgebra 1",
  "kind":         "Are You Ready?",
  "role":         "AYR",
  "ladder":       { "prev": "foundational arithmetic review", "self": "Prealgebra 1", "next": "Prealgebra 2" },
  "grading":      { "mode": "single", "total": 28, "need": 23 },
  "instructions": "Readiness check for Prealgebra 1. Bar: 23 of 28 correct.",
  "special":      "algA_ayr",
  "sections":     [ <Section>, ... ]
}
```

|Field         |Type     |Rule                                                                                     |
|--------------|---------|-----------------------------------------------------------------------------------------|
|`id`          |string   |Unique. Convention `<course-abbrev>-<pre\|post>`.                                        |
|`course`      |string   |Course this places into. For ladder courses, must match the ladder string exactly.       |
|`kind`        |string   |`Are You Ready?` or `Do You Know?`. Display label.                                       |
|`role`        |string   |`AYR` or `DYK`. Drives the recommendation branch (CONSTANTS §6).                         |
|`ladder`      |object   |`{prev, self, next}` course names, used verbatim in recommendation messages.             |
|`grading`     |object   |See grading modes below.                                                                 |
|`instructions`|string   |Shown above the instrument.                                                              |
|`special`     |string   |Optional. Only value in use is `algA_ayr` (the three-tier readiness logic, CONSTANTS §5).|
|`sections`    |Section[]|One or more.                                                                             |

Grading object, `single` mode: `{ "mode": "single", "total": <int>, "need": <int> }`. Pass if correct ≥ need. `total` should equal the item count.

Grading object, `fundps` mode: `{ "mode": "fundps", "fundTotal": <int>, "fundNeeded": <int>, "psTotal": <int>, "psNeeded": <int> }`. Pass if fund ≥ fundNeeded AND ps ≥ psNeeded. Every item in this instrument must carry a `group` of `"fund"` or `"ps"`, and the group totals should match `fundTotal` and `psTotal`.

### Section object

```json
{ "title": "Multi-digit multiplication & division", "items": [ <Item>, ... ] }
```

`title` is a display header. A DYK instrument may use the sentinel title `Do You Know? (mastery / skip-check)`, which the result view hides when it is the only section.

### Item object

```json
{
  "id":     "1a",
  "label":  "1(a)",
  "prompt": "305 × 12",
  "ans":    "3,660",
  "v":      3660,
  "accept": ["3660", "3,660"],
  "manual": false,
  "group":  "fund"
}
```

|Field   |Type          |Rule                                                                             |
|--------|--------------|---------------------------------------------------------------------------------|
|`id`    |string        |Unique within the instrument. Keys the response/marks maps, so it must be stable.|
|`label` |string        |Display label, e.g. `1(a)`.                                                      |
|`prompt`|string        |The question. Plain text or HTML; math may use `\( \)`.                          |
|`ans`   |string        |Canonical answer, shown on reveal.                                               |
|`v`     |number or null|Numeric value for auto-grading, or null for non-numeric.                         |
|`accept`|string[]      |Accepted string forms (each normalized before compare). May be empty.            |
|`manual`|boolean       |`true` = symbolic, self-marked by the student. `false` = auto-graded.            |
|`group` |string        |`"fund"` or `"ps"`. Required in `fundps` instruments, ignored in `single`.       |

For an auto-graded item (`manual: false`), supply at least one of `v` or a non-empty `accept`, or it can never be marked correct (CONSTANTS §8). For a manual item, `v` and `accept` are ignored; `ans` is what the student checks against.

## Invariants the seed script should enforce

- Every id in `byContest`, `order`, and `ladder` resolves to a real object.
- Each AMC test has exactly 25 problems and `answers.length == problems.length`.
- `answers` entries are `A`–`E` or null; a null answer's problem number is in `voided`.
- Problem shape matches the test `mode` (all `img` or all `latex`); LaTeX choices number exactly 5 and are non-empty.
- No `http`/`https` image src anywhere in problem content (all images are `data:` URIs), so the bundle stays offline.
- `single` grading: `need <= total` and `total == item count`. `fundps`: `fundNeeded <= fundTotal`, `psNeeded <= psTotal`, and group totals match.
- Ladder course strings exactly equal the matching instrument `course` and catalog `course` strings (the join is by exact string).

## How it assembles

The build merges both files into one object the app reads as `DATA`:

```
DATA = { tests, byContest, keyedTests, diag: <entire diag_data.json> }
```

then injects that plus the embedded KaTeX block into the HTML template. The seed script's job is to produce or validate the two JSON files; assembly into the final HTML is mechanical from there.
