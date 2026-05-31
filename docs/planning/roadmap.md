---
title: "AMC - Development Roadmap"
schema_type: planning
status: published
owner: core-maintainer
purpose: "Document the phased implementation plan and milestones."
tags:
  - planning
  - roadmap
component: Strategy
source: "/plan command generation"
---

> **Status**: Published | **Updated**: 2026-05-31

## TL;DR

Build the [server-backed AMC Trainer](./adr/adr-001-initial-architecture.md) in four phases:
foundation (app + Postgres + content schema), MVP core (accounts, exam runner, server-side
grading, persistence), diagnostics + recommendation, then polish. Target a usable v1 in
roughly 7-9 weeks of part-time work.

## Timeline Overview

```text
Phase 0: Foundation     ████░░░░░░░░░░░░░░░░ (1 wk)   - app skeleton, DB, content schema
Phase 1: MVP Core       ░░░░████████████░░░░ (3-4 wk) - accounts, exam runner, persistence
Phase 2: Diagnostics    ░░░░░░░░░░░░████████ (2-3 wk) - instruments + recommendation engine
Phase 3: Polish         ░░░░░░░░░░░░░░░░████ (1-2 wk) - a11y, mobile, coverage, deploy
Buffer                  (~1 wk)              - absorbs one slip week (illness/work crunch)
```

The 7-9 week range already folds in roughly one week of slack; a part-time solo schedule
should expect to use it. Treat phase gates, not the calendar, as the source of truth.

## Milestones

| Milestone | Target | Status | Dependencies |
|-----------|--------|--------|--------------|
| M0: App + DB skeleton runs | Wk 1 | Planned | None |
| M1: Content seeded from prototype | Wk 2 | Planned | M0 |
| M2: Accounts + exam runner persist | Wk 4-5 | Planned | M1 |
| M3: Diagnostics + recommendation | Wk 6-7 | Planned | M2 |
| M4: v1 polished and deployed | Wk 8-9 | Planned | M3 |

---

## Phase 0: Foundation (Week 1)

### Objective

Stand up the FastAPI app, database, and content schema the rest of the work builds on.

### Deliverables

- [ ] FastAPI app boots with existing config/correlation/security middleware wired in.
- [ ] PostgreSQL via docker-compose; async SQLAlchemy session dependency.
- [ ] Alembic configured; initial migration for all entities in the tech spec.
- [ ] `/api/v1/health` (extends existing `src/amc/api/health.py`) green in CI.
- [ ] React SPA (`frontend/`) and API served same-origin behind the reverse proxy; the
  generated OpenAPI client builds against the running app (see
  [ADR-002](./adr/adr-002-frontend-framework.md)).
- [ ] Automated PostgreSQL backup (pg_dump or volume snapshot) **plus a tested restore**,
  documented, so the core "progress persists" promise survives a lost volume.

### Success Criteria

- ✅ Clone -> `docker-compose up` -> app + DB + SPA healthy in < 15 minutes.
- ✅ CI (backend tests/Ruff/BasedPyright; frontend lint/typecheck/vitest) passes on the branch.
- ✅ `alembic upgrade head` creates every table.
- ✅ A restore from backup reproduces a seeded database (restore drill passes, not just backup).

### Tasks

| Task | Est. Hours | Status |
|------|------------|--------|
| FastAPI app factory + middleware wiring | 3 | Planned |
| docker-compose (app + Postgres + reverse proxy serving the SPA) | 3 | Planned |
| SQLAlchemy models + async session | 4 | Planned |
| Alembic init + first migration | 3 | Planned |
| Reverse-proxy same-origin wiring + OpenAPI client generation in CI | 3 | Planned |
| Automated DB backup + restore drill | 3 | Planned |

---

## Phase 1: MVP Core (Weeks 2-5)

### Objective

Deliver the ranked top priority: accounts plus a timed AMC runner whose results persist
across devices, graded on the server.

### Deliverables

- [ ] Content import: migrate the prototype's nine papers (and `keyedTests`) into the DB,
  extracting base64 images to `assets/` files. Documented, repeatable seed script.
- [ ] Invite-based accounts; Argon2 passwords; session-cookie login; student/coach roles.
- [ ] Catalog + attempt API (exams without keys; submit returns graded review).
- [ ] Refactored exam-runner frontend (timer, flag, palette) calling the API.
- [ ] Test attempts persisted and re-loadable on any device for the account.

### Success Criteria

- ✅ A paper submitted on one device appears in history on another (same account).
- ✅ No `correct_answer` in any pre-submission API response or page source.
- ✅ Server scores match the prototype (6-point, count, voided) on identical inputs.
- ✅ Adding one new paper needs no application HTML/JS change.

### User Stories

#### US-001: Take a timed AMC test

**As a** student **I want** to take a timed AMC paper and submit it **so that** I get a
score that is saved to my account.

**Acceptance Criteria**:

- [ ] Timer counts down from `duration_sec`; auto-submits at zero.
- [ ] Flag and palette navigation work as in the prototype.
- [ ] On submit, the server grades and stores the attempt; review shows correct answers.

**Tasks**:

| Task | Est. Hours | Status |
|------|------------|--------|
| Grading service (port `scoreTest`) + 100% unit tests | 5 | Planned |
| Exam catalog + submit endpoints | 5 | Planned |
| React exam-runner components (timer, flag, palette, review) on the generated client | 10 | Planned |

#### US-002: Log in and keep my history

**As a** student **I want** to log in **so that** my attempts follow me across devices.

**Acceptance Criteria**:

- [ ] Admin/coach creates an invite; student sets a password and logs in.
- [ ] Session persists via secure cookie; `/auth/me` returns the user.
- [ ] History endpoint returns only that user's attempts.

**Tasks**:

| Task | Est. Hours | Status |
|------|------------|--------|
| Auth: Argon2 + server-side sessions + RBAC dependency + login rate-limiting | 7 | Planned |
| Invite mint + register/redeem endpoints + onboarding page | 7 | Planned |
| Content ingestion: seed all AMC 8/10/12 papers + base64 asset extraction | 12 | Planned |

### Dependencies

- Requires: Phase 0 complete. Blocks: Phase 2.

---

## Phase 2: Diagnostics + Recommendation (Weeks 6-7)

### Objective

Reproduce the placement experience: the 10 AoPS instruments and the synthesized
recommendation.

### Deliverables

- [ ] Diagnostic instruments + items seeded; auto-grade and self-mark item handling.
- [ ] Diagnostic attempt endpoints returning verdict and recommendation message.
- [ ] Recommendation service (port `synthesize`, ladder + AMC gates) with unit tests.
- [ ] Progress dashboard: contest history, diagnostic table, combined read; coach view of a
  student's progress.

### Success Criteria

- ✅ `synthesize` output matches the prototype on the same attempt data.
- ✅ Self-marked symbolic items update the verdict on toggle (server-recomputed).
- ✅ A coach can open any student's progress; a student cannot open another's.

### User Stories

#### US-003: Get a placement recommendation

**As a** student **I want** my diagnostics and AMC score combined **so that** I see which
course to start. **Acceptance**: recommendation reflects latest attempts; matches prototype
logic.

---

## Phase 3: Polish (Weeks 8-9)

### Objective

Harden for real use: accessibility, mobile, correctness, coverage, deploy.

### Deliverables

- [ ] Coverage >= 80% line / 70% branch; grading + recommendation at 100%.
- [ ] Answer keys verified against the AoPS Wiki for all seeded papers.
- [ ] Responsive/mobile layout; keyboard navigation and basic a11y pass.
- [ ] Security review (auth, RBAC, key non-exposure, same-origin cookie posture); docs and
  CHANGELOG updated.
- [ ] Backup/restore drill re-run and documented in the deploy guide.

### Success Criteria

- ✅ All tests pass; no high/critical findings from Bandit/pip-audit.
- ✅ Lighthouse: exam page interactive < 2s; mobile usable.
- ✅ README + deploy guide let a new machine run the app end-to-end, including a restore.

### Tasks

| Task | Est. Hours | Status |
|------|------------|--------|
| Coverage to threshold | 6 | Planned |
| Accessibility + mobile pass | 5 | Planned |
| Answer-key verification | 4 | Planned |
| Security review + deploy guide | 5 | Planned |

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Image-to-LaTeX content effort underestimated | M | H | Keep image render mode; only convert opportunistically |
| Prototype scoring edge cases (voided, count mode) missed | M | M | Port with golden tests against prototype outputs |
| Auth/session security mistakes | L | H | Use vetted libraries; tech-spec security section; security review in Phase 3 |
| Cross-origin cookie-auth misconfig (SPA vs API) | M | M | Same-origin reverse proxy per ADR-002; validated in Phase 0 |
| Single-instance Postgres data loss | L | H | Automated backup + tested restore from Phase 0 (core "progress persists" promise) |
| Scope creep toward public product | M | M | PVS out-of-scope list; revisit ADR-001 if audience grows |
| Solo-developer bandwidth | M | M | Phase gates; ship Phase 1 value before Phase 2 |

## Definition of Done

A feature is complete when:

- [ ] Code reviewed and approved.
- [ ] Tests written and passing (meets coverage targets).
- [ ] Documentation updated.
- [ ] Ruff + BasedPyright clean; security scans clean.
- [ ] Merged to main via signed, conventional-commit PR.

## Related Documents

- [Project Vision](./project-vision.md)
- [Technical Spec](./tech-spec.md)
- [ADR-001: Server-Backed Architecture](./adr/adr-001-initial-architecture.md)
- [ADR-002: React 19 SPA Frontend](./adr/adr-002-frontend-framework.md)
