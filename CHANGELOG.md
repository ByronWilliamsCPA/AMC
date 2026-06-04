# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup and structure
- Diagnostic course catalog: `DiagnosticCatalogEntry` model and migration, seeded
  from `diag_data.json`, persisting how each course is reached (diagnostic /
  prereq / amc) and the AMC-10 score thresholds for gated courses
- `create-admin` bootstrap command (`python -m amc.create_admin`): creates the
  first staff account out-of-band since invite-only onboarding cannot bootstrap
  itself. Password read from `AMC_ADMIN_PASSWORD` or prompted (never a CLI
  argument); refuses to overwrite an existing account
- Backup and restore scripts (`scripts/backup.sh`, `scripts/restore.sh`) wrapping
  `pg_dump` / `psql` against the compose database service, plus a Deployment and
  Operations guide documenting setup, seeding, the first-admin bootstrap, and a
  step-by-step restore drill (Phase 0.6)

### Changed

- Wire AMC-10 score gates into the placement recommendation: the progress
  endpoint now sources `gate: "amc"` thresholds from the seeded catalog
  (CONSTANTS.md section 3) instead of passing an empty gate list, so a student's
  AMC-10 score unlocks the catalog courses it clears (Problem Series at 60+,
  Final Fives at 80+)
- Fix Python 3.10 compatibility (datetime.UTC replaced with timezone.utc;
  ruff target-version aligned with requires-python)
- Apply full repo-compliance audit: REUSE licensing, pre-commit hooks (no-em-dash,
  yamllint, markdownlint, basedpyright, detect-secrets), CI workflow fixes
  (CodeQL, REUSE, security scan, compatibility matrix, docs strict mode),
  settings.json permission syntax, and OpenSSF baseline improvements
- Raise test coverage above the 80% gate with targeted unit tests for
  seed.py, core security, auth schemas, and health endpoints

### Security

- Phase 3.4 security review (`docs/security-review.md`): no critical or high
  findings. Remediated a login user-enumeration timing channel (constant-work
  Argon2 verify for unknown emails), tightened the CORS credentials/headers
  posture, stopped the readiness probe from returning raw database errors to
  unauthenticated callers, and defaulted production to a single app replica so
  the in-process login rate limiter is not bypassed
- Remediate all 14 Dependabot dependency alerts on the frontend (npm) tree by
  upgrading `@hey-api/openapi-ts` 0.61 to 0.98 (clears the transitive
  `handlebars` and `tar` advisories and regenerates the API client) and `vitest`
  /`@vitest/coverage-v8` 3.x to 4.1 (clears the critical Vitest UI-server
  advisory). `npm audit` now reports 0 vulnerabilities. Drop the standalone
  `@hey-api/client-fetch` dependency, which openapi-ts 0.98 bundles internally,
  so it is no longer imported or installed
- Document the Python `py` 1.11.0 advisory (PYSEC-2022-42969) in
  `docs/known-vulnerabilities.md`: a dev-only transitive dependency of
  `interrogate` with no upstream fix and an unreachable Subversion code path

## [0.1.0] - TBD

### Added
- Initial project structure with Poetry package management
- Pydantic v2 JSON schema validation
- Structured logging with structlog and rich console output
- Pre-commit hooks (Ruff format, Ruff lint, BasedPyright, Bandit, pip-audit)
- Comprehensive test suite with pytest
- GitHub Actions CI/CD pipeline with quality gates
- CLI tool foundation
- License

### Documentation
- README with project overview and quick start
- CONTRIBUTING guidelines with development workflow
- References to williaby org-level Security Policy
- References to williaby org-level Code of Conduct

### Infrastructure
- Poetry dependency management with lock file
- pytest test framework with coverage reporting
- GitHub issue tracking and templates
- Automated dependency security scanning (Safety, Bandit)
- Code quality enforcement (Ruff, BasedPyright)
- CI/CD pipeline with multiple quality gates

### Security
- Bandit security linting
- Safety dependency vulnerability scanning
- Pre-commit hooks for security validation

[Unreleased]: https://github.com/williaby/amc/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/williaby/amc/releases/tag/v0.1.0
