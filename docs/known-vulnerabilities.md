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

To add new entries, see [.github/known-vulnerabilities-template.md](../.github/known-vulnerabilities-template.md).

## Active Entries

## GHSA-3mfm-83xf-c92r (and 7 related) | handlebars | Critical

| Field | Value |
|-------|-------|
| **CVE ID** | GHSA-3mfm-83xf-c92r, GHSA-2w6w-674q-4c4q, GHSA-2qvq-rjwj-gvw9, GHSA-7rx3-28cr-v5wh, GHSA-442j-39wm-28r2, GHSA-xhpv-hc6g-r9c6, GHSA-9cx6-37pm-9jff, GHSA-xjpj-3mr7-gcpf |
| **Package** | handlebars |
| **Affected Version** | 4.0.0 - 4.7.8 (4.7.8 installed) |
| **Fixed Version** | No fix in current range; requires upgrading @hey-api/openapi-ts to 0.98.0+ |
| **Severity** | Critical (3 critical, 1 high; 8 total advisories) |
| **CVSS Score** | N/A (GHSA only; no CVE CVSS assigned) |
| **Discovered** | 2026-06-01 |
| **Reassessment Due** | 2026-07-31 |
| **Blocking Release** | No |

### Description

Multiple vulnerabilities in Handlebars.js 4.7.8 including: JavaScript injection via AST
type confusion (prototype pollution), prototype pollution leading to XSS through partial
template injection, property access validation bypass, and denial of service via malformed
decorator syntax in template compilation.

### Impact on This Project

`handlebars` is a transitive devDependency, pulled in via
`@hey-api/openapi-ts@0.61.3`. It is used only during development as a code generation
tool that produces TypeScript API client stubs from OpenAPI schemas. The vulnerable
package is never bundled into the production build and is not shipped to end users.
The vulnerable code paths (template compilation, prototype access) are exercised only
when running `openapi-ts generate` on a developer machine or in CI, using a trusted
local OpenAPI schema. There is no attacker-controlled input to the Handlebars runtime
in this project.

### Remediation Plan

- [ ] Upgrade `@hey-api/openapi-ts` from `0.61.3` to `0.98.0+` (breaking change; see
  migration guide at https://heyapi.dev/openapi-ts/changelog)
- [ ] After upgrade, regenerate API client stubs and validate frontend compilation
- [ ] Target completion: before first production release

### Why Not Fixed Yet

`npm audit fix --force` would install `@hey-api/openapi-ts@0.98.0`, which is a breaking
change. The 0.98.x series has a different code generation API, configuration format, and
output structure. Migrating requires non-trivial effort to verify that all generated
client code continues to work correctly. Deferring until the initial implementation
milestone is complete to avoid scope creep on the current phase.

### References

- [GHSA-3mfm-83xf-c92r](https://github.com/advisories/GHSA-3mfm-83xf-c92r)
- [GHSA-2w6w-674q-4c4q](https://github.com/advisories/GHSA-2w6w-674q-4c4q)
- [GHSA-2qvq-rjwj-gvw9](https://github.com/advisories/GHSA-2qvq-rjwj-gvw9)
- [GHSA-7rx3-28cr-v5wh](https://github.com/advisories/GHSA-7rx3-28cr-v5wh)
- [GHSA-442j-39wm-28r2](https://github.com/advisories/GHSA-442j-39wm-28r2)
- [GHSA-xhpv-hc6g-r9c6](https://github.com/advisories/GHSA-xhpv-hc6g-r9c6)
- [GHSA-9cx6-37pm-9jff](https://github.com/advisories/GHSA-9cx6-37pm-9jff)
- [GHSA-xjpj-3mr7-gcpf](https://github.com/advisories/GHSA-xjpj-3mr7-gcpf)

---

## GHSA-34x7-hfp2-rc4v (and 5 related) | tar | High

| Field | Value |
|-------|-------|
| **CVE ID** | GHSA-34x7-hfp2-rc4v, GHSA-8qq5-rm4j-mr97, GHSA-83g3-92jg-28cx, GHSA-qffp-2rhf-9h96, GHSA-9ppj-qmqm-q256, GHSA-r6q2-hw4h-h46w |
| **Package** | tar |
| **Affected Version** | <=7.5.10 (6.2.1 installed) |
| **Fixed Version** | No fix in current range; requires upgrading @hey-api/openapi-ts to 0.98.0+ |
| **Severity** | High (4 high; 6 total advisories) |
| **CVSS Score** | N/A (GHSA only; no CVE CVSS assigned) |
| **Discovered** | 2026-06-01 |
| **Reassessment Due** | 2026-07-31 |
| **Blocking Release** | No |

### Description

Multiple path traversal and symlink poisoning vulnerabilities in `tar` (node-tar)
versions up to and including 7.5.10. Issues include: arbitrary file creation/overwrite
via hardlink path traversal, symlink poisoning via insufficient path sanitization,
hardlink target escape through symlink chains, drive-relative linkpath traversal, and
a race condition via Unicode ligature collisions on macOS APFS.

### Impact on This Project

`tar` is a transitive devDependency, pulled in via the chain:
`@hey-api/openapi-ts@0.61.3` -> `c12@2.0.1` -> `giget@1.2.5` -> `tar@6.2.1`.
It is used only when `giget` fetches remote templates during development-time code
generation. It is never present in the production build or shipped to end users.
The path traversal vulnerabilities are relevant when extracting untrusted archives;
in this project, `giget` fetches from known, trusted upstream sources. The attack
surface does not exist in production.

### Remediation Plan

- [ ] Upgrade `@hey-api/openapi-ts` from `0.61.3` to `0.98.0+` (same breaking upgrade
  that resolves the handlebars vulnerabilities above; both are fixed by the same
  upstream change)
- [ ] After upgrade, regenerate API client stubs and validate frontend compilation
- [ ] Target completion: before first production release

### Why Not Fixed Yet

Same blocker as the handlebars entry above: the fix requires upgrading
`@hey-api/openapi-ts` to 0.98.0+, a breaking change deferred until the initial
implementation milestone is complete. Both this entry and the handlebars entry above
are resolved by the same single upstream upgrade.

### References

- [GHSA-34x7-hfp2-rc4v](https://github.com/advisories/GHSA-34x7-hfp2-rc4v)
- [GHSA-8qq5-rm4j-mr97](https://github.com/advisories/GHSA-8qq5-rm4j-mr97)
- [GHSA-83g3-92jg-28cx](https://github.com/advisories/GHSA-83g3-92jg-28cx)
- [GHSA-qffp-2rhf-9h96](https://github.com/advisories/GHSA-qffp-2rhf-9h96)
- [GHSA-9ppj-qmqm-q256](https://github.com/advisories/GHSA-9ppj-qmqm-q256)
- [GHSA-r6q2-hw4h-h46w](https://github.com/advisories/GHSA-r6q2-hw4h-h46w)

## Resolved Entries

| CVE | Package | Resolved Date | Resolution |
|-----|---------|---------------|------------|

## Review History

| Review Date | Reviewer | Notes |
|-------------|----------|-------|
| 2026-06-01 | Byron Williams | Initial creation. Two npm devDependency vulnerabilities documented (handlebars, tar). Both resolved by upgrading @hey-api/openapi-ts to 0.98.0+. |
