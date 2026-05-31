# Content sources & provenance

Where the seeded AMC content came from, the exact URL patterns the build used,
the re-fetch steps, and the trust caveats. Complements [`README.md`](README.md),
[`CONTENT_CONTRACT.md`](CONTENT_CONTRACT.md), and [`CONSTANTS.md`](CONSTANTS.md).

> **Licensing reminder:** AMC problems are MAA-copyrighted, used here for personal
> study. Solutions are never embedded — each problem links out via its `sol`
> field. Keep content behind auth; never expose it to crawlers.

## Summary

| Contest | Problems / figures | Answer keys | Coverage |
|---------|--------------------|-------------|----------|
| AMC 8 | Po-Shen Loh LIVE archive | Po-Shen Loh answer PDFs (independent cross-check) | per bundled year |
| AMC 10 | `ryanrudes/amc` GitHub (problem scans) | Po-Shen Loh LIVE answer PDFs | AMC 10 only, 2002–2020 |
| AMC 12 | `randommath` community mirror (typeset → KaTeX HTML) | **official AoPS** answer-key pages | per bundled year |

The AoPS wiki (`artofproblemsolving.com/wiki`) is the canonical source for all of
this, but it sits behind Cloudflare and blocks automated access, so it could not
be scraped directly. It appears in the data only as the outbound `sol` solution
link per problem.

## AMC 8 — Po-Shen Loh LIVE archive

Problems, choices, diagrams, and a key cross-check all come from one source.

- **Contest data:** `https://live.poshenloh.com/past-contests/amc8/<year>`
  The full contest is embedded in the page's `__NEXT_DATA__` JSON under the key
  `pastContest-amc8-<year>`.
- **Diagrams:** SVGs at
  `https://live.poshenloh.com/images/past-contests/amc8/<year>/<n>.svg`
  (inlined into the problem HTML as `data:` URIs).
- **Answer-key PDF (independent cross-check):**
  `https://live.poshenloh.com/images/past-contests/pdf/amc8-<year>-answers.pdf`
  Keys were verified two independent ways (problem-data keys vs. this PDF); all
  three sources agreed for the bundled years.

## AMC 10 — split across two sources

- **Problem images:** the public GitHub archive
  [`ryanrudes/amc`](https://github.com/ryanrudes/amc). The build checked the repo
  out locally and read `amc-main/amcdata/AMC/10/<year>/<A|B>/<n>.png`; on GitHub
  the raw files live under `amcdata/AMC/10/...`. **Covers AMC 10 only, 2002–2020
  — no AMC 8/12 and no answer keys.**
- **Answer keys:** Po-Shen Loh LIVE answer PDFs,
  `https://live.poshenloh.com/images/past-contests/pdf/amc10-<year><A|B>-answers.pdf`.
  `answer_keys.json` (AMC 10 keys for 2010–2020) was assembled from these PDFs.

## AMC 12 — mirror problems, official keys

A deliberate split: the mirror's **problem text** is used, but its **keys are
not**.

- **Problems / figures:** the `randommath` community mirror,
  `https://wiki.randommath.com/amc12/<year>/part-<a|b>` (diagram images on its
  `/amc/` path). Rendered as pre-typeset KaTeX HTML.
- **Answer keys:** the **official AoPS answer-key pages** (not the mirror).
  Mirror-extracted keys were tried first and produced a wrong answer, so only the
  official AoPS keys are trusted. Treat AMC 12 **wording** as practice-grade; the
  **keys are official**.

## Re-fetching or extending the data

The goal is to refresh or add papers without reverse-engineering the build
scripts. For each contest, produce content in the shape defined by
[`CONTENT_CONTRACT.md`](CONTENT_CONTRACT.md), then run
[`validate_content.py`](validate_content.py) and re-seed
(`python -m amc.seed`).

- **AMC 8 (new year):** pull `__NEXT_DATA__` from the LIVE contest page; extract
  problems/choices and the `<n>.svg` diagrams (inline as `data:` URIs); take the
  key from the answers PDF.
- **AMC 10 (new year):** the GitHub archive stops at 2020 — supply problem scans
  in the contract's `img` (data-URI) shape and the key from a LIVE answers PDF.
- **AMC 12 (new year):** the mirror's problem text and figures already parse for
  additional years; the one thing each new paper needs is an **official AoPS
  answer-key screenshot** to source the key. (The 2025 AMC 12A was held back
  because its official key listed problem 25 as having no correct choice — use the
  `voided` mechanism for such defects.)

Always re-run the validator before seeding; it catches bad choice counts,
external image URLs, key/problem length mismatches, and broken ladder/catalog
joins.
