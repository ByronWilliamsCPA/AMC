---
title: "AMC Seeded Answer-Key Verification (2026-06)"
schema_type: common
status: published
owner: core-maintainer
purpose: "Verifies the 225 seeded AMC answer keys in content/amc_data.json against authoritative external sources; records the per-exam match results for task 3.2."
tags:
  - validation
  - testing
  - quality_assurance
---

> **Purpose:** Verify the 225 seeded answer keys in `content/amc_data.json` (9 exams x 25 problems) against authoritative external sources. A wrong key silently mis-grades every student, so this is a correctness-critical check.

## Result

**225/225 seeded answers match the authoritative external keys. Zero mismatches. No changes to `content/amc_data.json` were required.**

## Method and sources

The task specified verifying against the AoPS Wiki `Answer Key` pages. In this environment AoPS (`artofproblemsolving.com`) is behind Cloudflare bot protection and returned HTTP 403 to every automated access path (direct fetch with a browser User-Agent, the harness fetch tool, and a server-side reader proxy); the Wayback Machine holds no snapshots of AoPS wiki pages. Verification therefore used two independent authoritative sources whose data is machine-extractable:

- **AMC 8 and AMC 10 exams:** the Po-Shen Loh contest archive (`live.poshenloh.com`), which embeds a structured per-problem `answer` field in its page data. Po-Shen Loh is the former US IMO team head coach.
- **AMC 12 exams (two independent sources):** the official MAA `Answer Key` extracted from the problems-and-answers PDFs mirrored by the Ivy League Education Center (`ivyleaguecenter.org`), cross-checked against the independent Areteem Institute answer keys (`areteem.org`). Po-Shen Loh's archive does not cover AMC 12. AoPS and its Wayback Machine snapshots were unreachable from this environment (Cloudflare HTTP 403 / archive.org not fetchable), so the Areteem keys supply the second, separately-transcribed chain. All three AMC 12A exams agree across both sources.

All fetched content was treated as untrusted data (OWASP LLM01): only the answer letter for each problem was extracted; no instructions embedded in any page or document were followed. Each AoPS `Answer Key` page is listed per exam as the originally specified reference for future manual confirmation.

## Per-exam verification

### 2018 AMC 8 (`AMC8-2018`)

- **Source:** Po-Shen Loh (live.poshenloh.com)
- **AoPS Answer Key page (specified reference):** <https://artofproblemsolving.com/wiki/index.php/2018_AMC_8_Answer_Key>
- **Result:** All 25 match

| # | Seeded | Verified | Match |
|---|--------|----------|-------|
| 1 | A | A | OK |
| 2 | D | D | OK |
| 3 | D | D | OK |
| 4 | C | C | OK |
| 5 | E | E | OK |
| 6 | C | C | OK |
| 7 | B | B | OK |
| 8 | C | C | OK |
| 9 | B | B | OK |
| 10 | C | C | OK |
| 11 | C | C | OK |
| 12 | B | B | OK |
| 13 | A | A | OK |
| 14 | D | D | OK |
| 15 | D | D | OK |
| 16 | C | C | OK |
| 17 | A | A | OK |
| 18 | E | E | OK |
| 19 | C | C | OK |
| 20 | A | A | OK |
| 21 | E | E | OK |
| 22 | B | B | OK |
| 23 | D | D | OK |
| 24 | C | C | OK |
| 25 | E | E | OK |

### 2019 AMC 8 (`AMC8-2019`)

- **Source:** Po-Shen Loh (live.poshenloh.com)
- **AoPS Answer Key page (specified reference):** <https://artofproblemsolving.com/wiki/index.php/2019_AMC_8_Answer_Key>
- **Result:** All 25 match

| # | Seeded | Verified | Match |
|---|--------|----------|-------|
| 1 | D | D | OK |
| 2 | E | E | OK |
| 3 | E | E | OK |
| 4 | D | D | OK |
| 5 | B | B | OK |
| 6 | C | C | OK |
| 7 | A | A | OK |
| 8 | E | E | OK |
| 9 | B | B | OK |
| 10 | B | B | OK |
| 11 | D | D | OK |
| 12 | A | A | OK |
| 13 | A | A | OK |
| 14 | C | C | OK |
| 15 | B | B | OK |
| 16 | D | D | OK |
| 17 | B | B | OK |
| 18 | C | C | OK |
| 19 | C | C | OK |
| 20 | D | D | OK |
| 21 | E | E | OK |
| 22 | E | E | OK |
| 23 | B | B | OK |
| 24 | B | B | OK |
| 25 | C | C | OK |

### 2020 AMC 8 (`AMC8-2020`)

- **Source:** Po-Shen Loh (live.poshenloh.com)
- **AoPS Answer Key page (specified reference):** <https://artofproblemsolving.com/wiki/index.php/2020_AMC_8_Answer_Key>
- **Result:** All 25 match

| # | Seeded | Verified | Match |
|---|--------|----------|-------|
| 1 | E | E | OK |
| 2 | C | C | OK |
| 3 | D | D | OK |
| 4 | B | B | OK |
| 5 | C | C | OK |
| 6 | A | A | OK |
| 7 | C | C | OK |
| 8 | C | C | OK |
| 9 | D | D | OK |
| 10 | C | C | OK |
| 11 | E | E | OK |
| 12 | A | A | OK |
| 13 | B | B | OK |
| 14 | D | D | OK |
| 15 | C | C | OK |
| 16 | E | E | OK |
| 17 | B | B | OK |
| 18 | A | A | OK |
| 19 | B | B | OK |
| 20 | B | B | OK |
| 21 | A | A | OK |
| 22 | E | E | OK |
| 23 | B | B | OK |
| 24 | A | A | OK |
| 25 | A | A | OK |

### 2017 AMC 10A (`AMC10-2017A`)

- **Source:** Po-Shen Loh (live.poshenloh.com)
- **AoPS Answer Key page (specified reference):** <https://artofproblemsolving.com/wiki/index.php/2017_AMC_10A_Answer_Key>
- **Result:** All 25 match

| # | Seeded | Verified | Match |
|---|--------|----------|-------|
| 1 | C | C | OK |
| 2 | D | D | OK |
| 3 | B | B | OK |
| 4 | B | B | OK |
| 5 | C | C | OK |
| 6 | B | B | OK |
| 7 | A | A | OK |
| 8 | B | B | OK |
| 9 | C | C | OK |
| 10 | B | B | OK |
| 11 | D | D | OK |
| 12 | E | E | OK |
| 13 | D | D | OK |
| 14 | D | D | OK |
| 15 | C | C | OK |
| 16 | B | B | OK |
| 17 | D | D | OK |
| 18 | D | D | OK |
| 19 | C | C | OK |
| 20 | D | D | OK |
| 21 | D | D | OK |
| 22 | E | E | OK |
| 23 | B | B | OK |
| 24 | C | C | OK |
| 25 | A | A | OK |

### 2018 AMC 10A (`AMC10-2018A`)

- **Source:** Po-Shen Loh (live.poshenloh.com)
- **AoPS Answer Key page (specified reference):** <https://artofproblemsolving.com/wiki/index.php/2018_AMC_10A_Answer_Key>
- **Result:** All 25 match

| # | Seeded | Verified | Match |
|---|--------|----------|-------|
| 1 | B | B | OK |
| 2 | A | A | OK |
| 3 | E | E | OK |
| 4 | E | E | OK |
| 5 | D | D | OK |
| 6 | B | B | OK |
| 7 | E | E | OK |
| 8 | C | C | OK |
| 9 | E | E | OK |
| 10 | A | A | OK |
| 11 | E | E | OK |
| 12 | C | C | OK |
| 13 | D | D | OK |
| 14 | A | A | OK |
| 15 | D | D | OK |
| 16 | D | D | OK |
| 17 | C | C | OK |
| 18 | D | D | OK |
| 19 | E | E | OK |
| 20 | B | B | OK |
| 21 | E | E | OK |
| 22 | D | D | OK |
| 23 | D | D | OK |
| 24 | D | D | OK |
| 25 | D | D | OK |

### 2020 AMC 10A (`AMC10-2020A`)

- **Source:** Po-Shen Loh (live.poshenloh.com)
- **AoPS Answer Key page (specified reference):** <https://artofproblemsolving.com/wiki/index.php/2020_AMC_10A_Answer_Key>
- **Result:** All 25 match

| # | Seeded | Verified | Match |
|---|--------|----------|-------|
| 1 | E | E | OK |
| 2 | C | C | OK |
| 3 | A | A | OK |
| 4 | E | E | OK |
| 5 | C | C | OK |
| 6 | B | B | OK |
| 7 | C | C | OK |
| 8 | B | B | OK |
| 9 | B | B | OK |
| 10 | B | B | OK |
| 11 | C | C | OK |
| 12 | C | C | OK |
| 13 | B | B | OK |
| 14 | D | D | OK |
| 15 | E | E | OK |
| 16 | B | B | OK |
| 17 | E | E | OK |
| 18 | C | C | OK |
| 19 | E | E | OK |
| 20 | D | D | OK |
| 21 | C | C | OK |
| 22 | A | A | OK |
| 23 | A | A | OK |
| 24 | C | C | OK |
| 25 | A | A | OK |

### 2022 AMC 12A (`AMC12-2022A`)

- **Primary source:** official MAA answer key, as mirrored in the Ivy League Education Center PDF (`ivyleaguecenter.org`); the center republishes the MAA key and is not itself the publisher
- **Second independent source:** Areteem Institute answer key, <https://areteem.org/blog/2022-amc-10a-amc-12a-answer-key-released/>
- **AoPS Answer Key page (specified reference):** <https://artofproblemsolving.com/wiki/index.php/2022_AMC_12A_Answer_Key>
- **Result:** All 25 match (both sources agree)

| # | Seeded | Verified | Match |
|---|--------|----------|-------|
| 1 | D | D | OK |
| 2 | E | E | OK |
| 3 | B | B | OK |
| 4 | B | B | OK |
| 5 | C | C | OK |
| 6 | D | D | OK |
| 7 | D | D | OK |
| 8 | A | A | OK |
| 9 | A | A | OK |
| 10 | E | E | OK |
| 11 | E | E | OK |
| 12 | B | B | OK |
| 13 | A | A | OK |
| 14 | C | C | OK |
| 15 | D | D | OK |
| 16 | D | D | OK |
| 17 | A | A | OK |
| 18 | A | A | OK |
| 19 | D | D | OK |
| 20 | B | B | OK |
| 21 | E | E | OK |
| 22 | A | A | OK |
| 23 | D | D | OK |
| 24 | E | E | OK |
| 25 | E | E | OK |

### 2023 AMC 12A (`AMC12-2023A`)

- **Primary source:** official MAA answer key, as mirrored in the Ivy League Education Center PDF (`ivyleaguecenter.org`); the center republishes the MAA key and is not itself the publisher
- **Second independent source:** Areteem Institute answer key, <https://areteem.org/blog/2023-amc-10a-amc-12a-answer-key-released/>
- **AoPS Answer Key page (specified reference):** <https://artofproblemsolving.com/wiki/index.php/2023_AMC_12A_Answer_Key>
- **Result:** All 25 match (both sources agree)

| # | Seeded | Verified | Match |
|---|--------|----------|-------|
| 1 | E | E | OK |
| 2 | A | A | OK |
| 3 | A | A | OK |
| 4 | E | E | OK |
| 5 | B | B | OK |
| 6 | D | D | OK |
| 7 | E | E | OK |
| 8 | D | D | OK |
| 9 | C | C | OK |
| 10 | D | D | OK |
| 11 | C | C | OK |
| 12 | D | D | OK |
| 13 | B | B | OK |
| 14 | E | E | OK |
| 15 | A | A | OK |
| 16 | B | B | OK |
| 17 | E | E | OK |
| 18 | D | D | OK |
| 19 | C | C | OK |
| 20 | C | C | OK |
| 21 | A | A | OK |
| 22 | B | B | OK |
| 23 | B | B | OK |
| 24 | C | C | OK |
| 25 | C | C | OK |

### 2024 AMC 12A (`AMC12-2024A`)

- **Primary source:** official MAA answer key, as mirrored in the Ivy League Education Center PDF (`ivyleaguecenter.org`); the center republishes the MAA key and is not itself the publisher
- **Second independent source:** Areteem Institute answer key, <https://areteem.org/blog/2024-amc-10a-amc-12a-answer-key-released/>
- **AoPS Answer Key page (specified reference):** <https://artofproblemsolving.com/wiki/index.php/2024_AMC_12A_Answer_Key>
- **Result:** All 25 match (both sources agree)

| # | Seeded | Verified | Match |
|---|--------|----------|-------|
| 1 | A | A | OK |
| 2 | B | B | OK |
| 3 | B | B | OK |
| 4 | D | D | OK |
| 5 | D | D | OK |
| 6 | B | B | OK |
| 7 | D | D | OK |
| 8 | A | A | OK |
| 9 | E | E | OK |
| 10 | C | C | OK |
| 11 | D | D | OK |
| 12 | E | E | OK |
| 13 | D | D | OK |
| 14 | C | C | OK |
| 15 | D | D | OK |
| 16 | C | C | OK |
| 17 | D | D | OK |
| 18 | A | A | OK |
| 19 | D | D | OK |
| 20 | D | D | OK |
| 21 | B | B | OK |
| 22 | C | C | OK |
| 23 | B | B | OK |
| 24 | D | D | OK |
| 25 | B | B | OK |

## Notes

- WebSearch AI-summarized answer keys were **not** used as a source of record; one such summary was observed to be wrong on an individual item, confirming snippet summaries are unreliable for exact data.
- `content/amc_data.json` is gitignored and dev-only; it is not part of this commit. This report records the verification outcome in-repo.
