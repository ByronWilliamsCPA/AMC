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
- Apply full repo-compliance audit: REUSE licensing, pre-commit hooks (no-em-dash,
  yamllint, markdownlint, basedpyright, detect-secrets), CI workflow fixes
  (CodeQL, REUSE, security scan, compatibility matrix, docs strict mode),
  settings.json permission syntax, and OpenSSF baseline improvements
- Raise test coverage from 76.68% to 80.51% with targeted unit tests for
  seed.py, core security, auth schemas, and health endpoints
- Fix Python 3.10 compatibility (datetime.UTC replaced with timezone.utc;
  ruff target-version aligned with requires-python)

- Apply full repo-compliance audit: REUSE licensing, pre-commit hooks (no-em-dash,
  yamllint, markdownlint, basedpyright, detect-secrets), CI workflow fixes
  (CodeQL, REUSE, security scan, compatibility matrix, docs strict mode),
  settings.json permission syntax, and OpenSSF baseline improvements
- Raise test coverage from 76.68% to 80.51% with targeted unit tests for
  seed.py, core security, auth schemas, and health endpoints
- Fix Python 3.10 compatibility (datetime.UTC replaced with timezone.utc;
  ruff target-version aligned with requires-python)

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
