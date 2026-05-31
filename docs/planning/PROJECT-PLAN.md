---
title: "AMC Trainer - Project Plan"
schema_type: planning
status: published
owner: core-maintainer
purpose: "Synthesized project plan with git branch strategy, phase deliverables, and quality gates."
tags:
  - planning
  - project-plan
component: Strategy
---

> **Status**: Published | **Version**: 1.0 | **Synthesized**: 2026-05-31
>
> Source documents: [project-vision.md](./project-vision.md),
> [tech-spec.md](./tech-spec.md), [roadmap.md](./roadmap.md),
> [ADR-001](./adr/adr-001-initial-architecture.md),
> [ADR-002](./adr/adr-002-frontend-framework.md)

---

## Executive Summary

AMC Trainer replaces a 4.6MB single-file prototype with a server-backed web app that
gives a math coach and up to 30 students persistent, cross-device access to timed AMC
8/10/12 practice tests and AoPS placement diagnostics. A recommendation engine synthesizes
both signals into a starting-course suggestion. The scope is a private, invite-only group;
no public signup, no billing, no authoring UI.

---

## Scope

### In Scope (v1)

| Capability | Notes |
|------------|-------|
| AMC 8/10/12 timed practice tests | Nine seeded papers plus an import path for more |
| Server-side grading | Answer keys never leave the server (closes prototype's key leak) |
| AoPS placement diagnostics | 10 instruments; auto-graded and self-marked items |
| Recommendation engine | Ladder + AMC-gate synthesis ported from prototype |
| Invite-based accounts | Student and coach roles; no open signup |
| Cross-device persistence | All attempts stored in PostgreSQL |
| Coach progress view | Coach can read any student's progress |
| Content model | Problems as DB rows; images as files under `assets/` |

### Out of Scope (v1)

- Public self-service signup, billing, or marketing site
- Problem-authoring UI (v1 uses seed/import scripts)
- Auto-grading symbolic answers (self-mark is kept from the prototype)
- Adaptive practice, spaced repetition, per-topic drills
- Native mobile apps (responsive web only)
- Object-storage/CDN for assets (deferred; revisit on scale)

---

## Architecture Overview

| ADR | Decision | Rationale |
|-----|----------|-----------|
| [ADR-001](./adr/adr-001-initial-architecture.md) | FastAPI + PostgreSQL (async SQLAlchemy) modular-monolith backend | Only option that achieves cross-device persistence, multi-user accounts, and server-side grading simultaneously, using the existing scaffolded dependencies |
| [ADR-002](./adr/adr-002-frontend-framework.md) | React 19 + TypeScript + Vite SPA, same-origin reverse proxy | Stateful exam runner scales better with a component model; generated OpenAPI client provides a type-safe API contract; stays on the cookiecutter template's golden path |

### Deployment Topology (from ADR-002)

```text
            +----------- reverse proxy (one origin) -----------+
client --►  |  /api/*  ─► FastAPI (uvicorn)   /*  ─► React SPA |
            +---------------------------------------------------+
```

Both app and SPA share a single origin, so the `HTTP-only Secure SameSite=Lax` session
cookie is valid without CORS-with-credentials relaxation. Problem images under `assets/`
are served through the authenticated API, not as unauthenticated static files.

---

## Technology Stack

### Backend

| Layer | Choice |
|-------|--------|
| Language | Python 3.12 (supports >=3.10,<3.15) |
| Package manager | UV |
| Framework | FastAPI >= 0.120, Uvicorn[standard] >= 0.23 |
| Validation | Pydantic v2 + pydantic-settings |
| ORM | SQLAlchemy 2.0 (asyncio) + asyncpg |
| Migrations | Alembic |
| Auth | Argon2 (argon2-cffi); server-side sessions backed by `Session` table |
| Linter/formatter | Ruff (88 chars, PyStrict-aligned) |
| Type checker | BasedPyright (strict) |
| Testing | pytest + pytest-asyncio + coverage |

### Frontend

| Layer | Choice |
|-------|--------|
| Framework | React 19 + TypeScript 5.7 |
| Build | Vite 6 |
| API client | axios + `@hey-api/openapi-ts` generated client (checked for drift in CI) |
| Math | KaTeX (auto-render) |
| Testing | vitest + testing-library |
| Quality | eslint, prettier |

### Infrastructure

| Concern | Tool |
|---------|------|
| Containerisation | Docker + docker-compose (app + Postgres + reverse proxy) |
| Proxy config | `frontend/nginx.conf` |
| CI/CD | GitHub Actions (CI, security, docs, publish already scaffolded) |
| DB backup | pg_dump or volume snapshot; restore drill documented |

---

## Phased Development

### Quality Gates (all phases)

Every phase branch must pass these gates before merge to `main`:

| Gate | Threshold |
|------|-----------|
| Line coverage | >= 80% overall; 100% on grading and recommendation services |
| Branch coverage | >= 70% overall |
| Ruff | Zero errors and zero warnings |
| BasedPyright | Strict; zero errors |
| Bandit | No HIGH or CRITICAL findings |
| pip-audit | No HIGH or CRITICAL vulnerabilities |
| Commits | Signed (`git commit -S`), conventional commit format |
| Pre-commit | `pre-commit run --all-files` passes |
| Frontend | `vitest` passes; OpenAPI client regeneration produces no diff |

---

### Phase 0: Foundation

**Branch:** `chore/phase-0-foundation`
**Milestone:** M0 + first half of M1 | **Timeline:** Week 1

**Goal:** Stand up the FastAPI app, PostgreSQL, Alembic migrations, and the same-origin
reverse-proxy topology so every subsequent phase builds on a proven, runnable skeleton.

#### Deliverables

| # | Deliverable |
|---|-------------|
| 0.1 | FastAPI app boots with existing config/correlation/security middleware wired in |
| 0.2 | PostgreSQL via docker-compose; async SQLAlchemy session dependency |
| 0.3 | Alembic configured; initial migration creates all entities from the tech spec |
| 0.4 | `/api/v1/health` green in CI |
| 0.5 | React SPA and API served same-origin behind the reverse proxy; generated OpenAPI client builds against the running app ([ADR-002](./adr/adr-002-frontend-framework.md)) |
| 0.6 | Automated PostgreSQL backup (pg_dump or volume snapshot) **plus a tested restore**, documented (reconciliation addition; durable progress is the core value) |

#### Acceptance Criteria (from roadmap)

- Clone -> `docker-compose up` -> app + DB + SPA healthy in < 15 minutes.
- CI (backend Ruff/BasedPyright/tests; frontend lint/typecheck/vitest) passes on the branch.
- `alembic upgrade head` creates every table without errors.
- A restore from backup reproduces a seeded database (restore drill passes, not just backup).

#### Phase 0 Quality Gates

All standard gates above apply. Coverage threshold may be waived for skeleton code pending
Phase 1 test additions, with a note in the PR explaining the gap and the plan.

#### Dependencies

None (first phase).

---

### Phase 1: MVP Core

**Branch:** `feat/phase-1-mvp-core`
**Milestone:** M1 + M2 | **Timeline:** Weeks 2-5

**Goal:** Deliver the highest-ranked capability: invite-based accounts, a timed AMC exam
runner, server-side grading, and persistent cross-device history.

#### Deliverables

| # | Deliverable |
|---|-------------|
| 1.1 | Content import: nine prototype papers seeded into DB; base64 images extracted to `assets/`; documented repeatable seed script |
| 1.2 | Invite-based accounts; Argon2 passwords; server-side sessions; student/coach roles |
| 1.3 | Login rate-limiting (reconciliation addition; open assumption from project-vision.md) |
| 1.4 | Grading service (`score_exam`): 6-point, count, voided modes; 100% unit test coverage |
| 1.5 | Catalog + attempt API endpoints (exams served without answer keys; submit returns graded review) |
| 1.6 | React exam-runner components (timer, flag, palette, review) on the generated OpenAPI client |
| 1.7 | Test attempts persisted and re-loadable on any device for the same account |

#### Acceptance Criteria (from roadmap)

- A paper submitted on one device appears in history on a second device (same account).
- No `correct_answer` field appears in any pre-submission API response or page source.
- Server scores match the prototype (6-point, count, voided) on identical inputs.
- Adding one new paper requires no change to application HTML/JS.

**US-001 (Take a timed AMC test):**

- Timer counts down from `duration_sec`; auto-submits at zero.
- Flag and palette navigation work as in the prototype.
- On submit, the server grades and stores the attempt; review shows correct answers.

**US-002 (Log in and keep history):**

- Admin/coach creates an invite; student sets a password and logs in.
- Session persists via secure cookie; `/auth/me` returns the authenticated user.
- History endpoint returns only that user's attempts.

#### Dependencies

Requires Phase 0 complete. Blocks Phase 2.

---

### Phase 2: Diagnostics + Recommendation

**Branch:** `feat/phase-2-diagnostics-recommendation`
**Milestone:** M3 | **Timeline:** Weeks 6-7

**Goal:** Reproduce the placement experience: the 10 AoPS instruments and the synthesized
starting-course recommendation.

#### Deliverables

| # | Deliverable |
|---|-------------|
| 2.1 | Diagnostic instruments + items seeded; auto-grade and self-mark item handling |
| 2.2 | Diagnostic attempt endpoints returning verdict and recommendation message |
| 2.3 | Recommendation service (`synthesize`): ladder walk + AMC gates ported from prototype; 100% unit test coverage |
| 2.4 | Progress dashboard: contest history, diagnostic table, combined placement read |
| 2.5 | Coach view of any student's progress; RBAC enforcement (students cannot see each other) |

#### Acceptance Criteria (from roadmap)

- `synthesize` output matches the prototype on the same attempt data.
- Self-marked symbolic items update the verdict on toggle (server-recomputed).
- A coach can open any student's progress; a student cannot open another's.

**US-003 (Get a placement recommendation):**

- Recommendation reflects the latest attempts.
- Recommendation matches prototype logic on identical input data.

#### Dependencies

Requires Phase 1 complete. Blocks Phase 3.

---

### Phase 3: Polish

**Branch:** `feat/phase-3-polish`
**Milestone:** M4 | **Timeline:** Weeks 8-9

**Goal:** Harden for real use: accessibility, mobile responsiveness, correctness
verification, full coverage, and a deploy guide.

#### Deliverables

| # | Deliverable |
|---|-------------|
| 3.1 | Coverage >= 80% line / 70% branch; grading + recommendation services at 100% |
| 3.2 | Answer keys verified against the AoPS Wiki for all seeded papers |
| 3.3 | Responsive/mobile layout; keyboard navigation; basic a11y pass |
| 3.4 | Security review: auth, RBAC, key non-exposure, same-origin cookie posture |
| 3.5 | CHANGELOG and deploy docs updated |
| 3.6 | Backup/restore drill re-run and documented in the deploy guide |

#### Acceptance Criteria (from roadmap)

- All tests pass; no HIGH/CRITICAL findings from Bandit/pip-audit.
- Lighthouse: exam page interactive < 2s; mobile layout usable.
- README + deploy guide let a new machine run the app end-to-end, including a restore.

#### Dependencies

Requires Phase 2 complete.

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Image-to-LaTeX content effort underestimated | Medium | High | Keep image render mode; only convert opportunistically |
| Prototype scoring edge cases (voided, count mode) missed | Medium | Medium | Port with golden tests against prototype outputs; 100% coverage on grading service |
| Auth/session security mistakes | Low | High | Use vetted libraries (argon2-cffi); follow tech-spec security section; security review in Phase 3 |
| Cross-origin cookie-auth misconfig | Medium | Medium | Same-origin reverse proxy per ADR-002; validated in Phase 0 success criteria |
| Single-instance Postgres data loss | Low | High | Automated backup + tested restore is a named Phase 0 deliverable |
| AMC/AoPS content redistribution | Low | High | Content behind auth (never publicly crawlable); MAA/AoPS attribution retained; takedown-response posture |
| Scope creep toward public product | Medium | Medium | PVS out-of-scope list enforced; revisit ADR-001 if audience grows beyond ~30 |
| Solo-developer bandwidth | Medium | Medium | Phase gates; ship Phase 1 value before Phase 2 |

---

## Success Metrics

| Metric | Before (prototype) | v1 Target |
|--------|--------------------|-----------|
| Cross-device continuity | 0% (localStorage) | 100% of attempts visible on a second device |
| Tracked students | 1 (hardcoded) | Up to 30 |
| Content onboarding | Hours of hand-editing a 4.6MB file | < 15 minutes via seed/import workflow |
| Answer-key integrity | Keys exposed in page source | Keys never in any pre-submission response |

---

## Phase 0 Checklist (Immediate Execution)

Tasks to complete on the `chore/phase-0-foundation` branch before any feature work begins:

- [ ] Create branch: `git checkout -b chore/phase-0-foundation`
- [ ] Wire FastAPI app factory with existing config, correlation, and security middleware
- [ ] Add `docker-compose.yml` services: FastAPI app, PostgreSQL 16, reverse proxy (nginx)
- [ ] Configure `frontend/nginx.conf` to proxy `/api/*` to FastAPI and `/*` to built SPA
- [ ] Define SQLAlchemy 2.0 async models for all entities in tech-spec.md (User, Invite, Session, Exam, Problem, DiagnosticInstrument, DiagnosticItem, TestAttempt, DiagnosticAttempt)
- [ ] `alembic init`; write and apply initial migration
- [ ] Implement `/api/v1/health` endpoint (extend existing `src/amc/api/health.py`)
- [ ] Add frontend lint/typecheck/vitest and OpenAPI-client drift check to CI
- [ ] Set up automated pg_dump backup script; document the restore procedure
- [ ] Run restore drill on a seeded database; confirm success and commit evidence to the deploy guide
- [ ] Verify: `docker-compose up` brings the full stack to healthy in < 15 minutes
- [ ] Verify: `pre-commit run --all-files` passes
- [ ] Open PR with signed conventional commit: `chore: add phase-0 foundation skeleton`

---

## Definition of Done

A phase is complete when:

- [ ] All phase deliverables merged to `main` via signed, conventional-commit PRs.
- [ ] All quality gates pass (see table above).
- [ ] Documentation and CHANGELOG updated for any user-visible change.
- [ ] Phase acceptance criteria verified and checked off in this document.

---

## Related Documents

- [Project Vision](./project-vision.md): problem statement, scope, constraints, and success metrics
- [Technical Specification](./tech-spec.md): data model, API endpoints, security, and performance targets
- [Development Roadmap](./roadmap.md): phased milestones, timeline estimates, and risk register
- [ADR-001: Server-Backed Architecture](./adr/adr-001-initial-architecture.md): FastAPI + PostgreSQL decision
- [ADR-002: React 19 SPA Frontend](./adr/adr-002-frontend-framework.md): React + same-origin proxy decision
