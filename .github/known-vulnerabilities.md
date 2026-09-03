# Known Vulnerabilities

This document tracks CVEs and security advisories that have been identified but cannot
be immediately remediated. Entries must be reviewed within 60 days of the Discovered
date. Any entry older than 60 days without reassessment blocks releases per the OpenSSF
release gate policy.

To add new entries, see [known-vulnerabilities-template.md](known-vulnerabilities-template.md).

## Active Entries

## PYSEC-2026-89 | markdown | High

| Field | Value |
|-------|-------|
| **CVE ID** | PYSEC-2026-89 |
| **Package** | markdown |
| **Affected Version** | 3.10.2 |
| **Fixed Version** | Fixed only in 3.8.1-3.8.2; no fixed release available for >=3.9 as of 2026-05-21 |
| **Severity** | High |
| **CVSS Score** | 7.5 |
| **Discovered** | 2026-05-21 |
| **Reassessment Due** | 2026-07-20 |
| **Blocking Release** | No |

### Description

DoS via malformed HTML-like sequences that cause `html.parser.HTMLParser` to raise
an unhandled `AssertionError` during Markdown parsing. Python-Markdown does not
catch this exception, so any application parsing attacker-controlled Markdown may
crash. Enables remote unauthenticated Denial of Service in web applications,
documentation systems, CI/CD pipelines, and any service rendering untrusted Markdown.
Also known as CVE-2025-69534 and GHSA-5wmx-573v-2qwq.

### Impact on This Project

The `markdown` package is a transitive dependency of `mkdocs`, `mkdocs-material`,
and related documentation tools. It is present only in the development environment
(docs tooling). This project does not parse attacker-controlled Markdown input at
runtime. The vulnerability is not exploitable in production. Dev-only impact.

### Remediation Plan

- [ ] Monitor the `markdown` package for a release that fixes PYSEC-2026-89 in
  the 3.9+ series
- [ ] Evaluate pinning `markdown` to `3.8.2` if compatible with `mkdocs` and
  `mkdocs-material` dependencies
- [ ] Reassess by 2026-07-20 whether a fixed version is available or whether
  mkdocs has migrated to a safe markdown version

### Why Not Fixed Yet

The fix landed in `markdown` 3.8.1, but the package subsequently released 3.9 and
3.10.x without incorporating the fix (or re-introduced the vulnerable code path).
As of 2026-05-21, no version in the 3.9+ series resolves this CVE. Downgrading to
3.8.2 may conflict with `mkdocs-material` and other tooling that requires 3.9+.

### References

- [PYSEC-2026-89](https://osv.dev/vulnerability/PYSEC-2026-89)
- [GitHub Advisory GHSA-5wmx-573v-2qwq](https://github.com/advisories/GHSA-5wmx-573v-2qwq)

## Resolved Entries

| CVE | Package | Resolved Date | Resolution |
|-----|---------|---------------|------------|
| PYSEC-2022-42969 (CVE-2022-42969, GHSA-w596-4wvx-j9j6) | py | 2026-09-03 | OSV withdrew the advisory on 2026-06-09; osv-scanner reported the ignore entry as unused. Entry removed from osv-scanner.toml. |

## Review History

| Review Date | Reviewer | Notes |
|-------------|----------|-------|
| 2026-MM-DD | Byron Williams | Initial creation. |
| 2026-09-03 | Claude Sonnet 4.6 | Removed the PYSEC-2022-42969 entry; OSV withdrew the advisory 2026-06-09, and the ignore in osv-scanner.toml was breaking Security Gate Validation with an "unused ignores" error. |
