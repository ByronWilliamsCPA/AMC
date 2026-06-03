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

## PYSEC-2022-42969 | py | Low

| Field | Value |
|-------|-------|
| **CVE ID** | PYSEC-2022-42969 (CVE-2022-42969) |
| **Package** | py |
| **Affected Version** | <=1.11.0 (1.11.0 installed) |
| **Fixed Version** | None (package unmaintained; 1.11.0 is the final release) |
| **Severity** | Low (ReDoS, dev-only, unreachable code path) |
| **CVSS Score** | 7.5 (AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H) per NVD; effective risk Low in context |
| **Discovered** | 2026-06-03 |
| **Reassessment Due** | 2026-08-02 |
| **Blocking Release** | No |

### Description

The `py` library through 1.11.0 is vulnerable to a Regular Expression Denial of
Service (ReDoS) via a Subversion repository with crafted info data: the
`py.path.svnwc` Subversion working-copy support mishandles the `InfoSvnCommand`
argument. Exploitation requires the application to invoke `py`'s Subversion path
handling against attacker-controlled SVN output.

### Impact on This Project

`py` is a transitive devDependency, pulled in via `interrogate@1.7.0` (the
docstring-coverage tool run in pre-commit and CI). It is never imported by
application code and never present in the production build or shipped to end
users. The vulnerable code path is `py.path.svnwc` (Subversion working-copy
support); this project uses Git, not Subversion, and `interrogate` never invokes
`py`'s SVN handling. There is no attacker-controlled SVN input anywhere in the
toolchain, so the ReDoS surface does not exist in practice.

### Remediation Plan

- [ ] No upstream fix exists: `py` is unmaintained and 1.11.0 is its final
  release. Track `interrogate` for a release that drops the `py` dependency, or
  evaluate replacing `interrogate` (e.g. with `docstr-coverage`) if the
  advisory's effective risk ever rises.
- [ ] Reassess on or before 2026-08-02.

### Why Not Fixed Yet

There is no patched version to upgrade to. The dependency is dev-only and the
vulnerable Subversion code path is never reached, so removing `interrogate`
solely for this finding is not justified at this time.

### References

- [PYSEC-2022-42969](https://github.com/pypa/advisory-database/blob/main/vulns/py/PYSEC-2022-42969.yaml)
- [CVE-2022-42969](https://nvd.nist.gov/vuln/detail/CVE-2022-42969)

## Resolved Entries

| CVE | Package | Resolved Date | Resolution |
|-----|---------|---------------|------------|
| GHSA-3mfm-83xf-c92r (and 7 related) | handlebars | 2026-06-03 | Upgraded `@hey-api/openapi-ts` 0.61.2 -> 0.98.1; handlebars is no longer present in the dependency tree (`npm audit` clean). Client regenerated and frontend gates pass. |
| GHSA-34x7-hfp2-rc4v (and 5 related) | tar | 2026-06-03 | Same `@hey-api/openapi-ts` 0.98.1 upgrade; the `c12`/`giget`/`tar` chain is gone (`npm audit` clean). |
| GHSA-5xrq-8626-4rwp | vitest, @vitest/coverage-v8 | 2026-06-03 | Upgraded `vitest` and `@vitest/coverage-v8` 3.x -> 4.1.8. Test suite passes (36/36) on vitest 4. |

## Review History

| Review Date | Reviewer | Notes |
|-------------|----------|-------|
| 2026-06-01 | Byron Williams | Initial creation. Two npm devDependency vulnerabilities documented (handlebars, tar). Both resolved by upgrading @hey-api/openapi-ts to 0.98.0+. |
| 2026-06-03 | Byron Williams | Resolved all three npm devDependency findings (handlebars, tar, vitest) via the openapi-ts 0.98.1 and vitest 4.1.8 upgrades; `npm audit` reports 0 vulnerabilities. Added the Python `py` 1.11.0 (PYSEC-2022-42969) finding: dev-only, unreachable SVN code path, no upstream fix available. |
