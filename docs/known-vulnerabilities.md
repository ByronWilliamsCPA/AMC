---
title: "Known Vulnerabilities"
schema_type: common
status: published
owner: core-maintainer
purpose: "Tracks known vulnerabilities that cannot be immediately resolved, per CLAUDE.md policy."
tags:
  - security
  - dependencies
---

This document tracks CVEs and security advisories that have been identified but cannot
be immediately remediated. Entries must be reviewed within 60 days of the Discovered
date. Any entry older than 60 days without reassessment blocks releases per the OpenSSF
release gate policy.

To add new entries, see `.github/known-vulnerabilities-template.md`.

## Active Entries

_No active entries currently._

## Resolved Entries

| CVE | Package | Resolved Date | Resolution |
|-----|---------|---------------|------------|
| GHSA-3mfm-83xf-c92r (and 7 related) | handlebars | 2026-06-03 | Upgraded `@hey-api/openapi-ts` 0.61.2 -> 0.98.1; handlebars is no longer present in the dependency tree (`npm audit` clean). Client regenerated and frontend gates pass. |
| GHSA-34x7-hfp2-rc4v (and 5 related) | tar | 2026-06-03 | Same `@hey-api/openapi-ts` 0.98.1 upgrade; `tar` is no longer pulled in (`c12`/`giget` upgraded to 3.x and dropped the vulnerable `tar`; `npm audit` clean). |
| GHSA-5xrq-8626-4rwp | vitest, @vitest/coverage-v8 | 2026-06-03 | Upgraded `vitest` and `@vitest/coverage-v8` 3.x -> 4.1.8. Test suite passes (36/36) on vitest 4. |
| PYSEC-2022-42969 (CVE-2022-42969, GHSA-w596-4wvx-j9j6) | py | 2026-09-03 | OSV withdrew the advisory on 2026-06-09; osv-scanner reports the ignore entry as unused. Entry removed from osv-scanner.toml. |

## Review History

| Review Date | Reviewer | Notes |
|-------------|----------|-------|
| 2026-06-01 | Byron Williams | Initial creation. Two npm devDependency vulnerabilities documented (handlebars, tar). Both resolved by upgrading @hey-api/openapi-ts to 0.98.0+. |
| 2026-06-03 | Byron Williams | Resolved all three npm devDependency findings (handlebars, tar, vitest) via the openapi-ts 0.98.1 and vitest 4.1.8 upgrades; `npm audit` reports 0 vulnerabilities. Added the Python `py` 1.11.0 (PYSEC-2022-42969) finding: dev-only, unreachable SVN code path, no upstream fix available. |
| 2026-09-03 | Claude Sonnet 4.6 | Removed the PYSEC-2022-42969 entry; OSV withdrew the advisory 2026-06-09, and the ignore in osv-scanner.toml was breaking Security Gate Validation with an "unused ignores" error. |
