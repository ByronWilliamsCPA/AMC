---
title: "ADR-001: Server-Backed Architecture with FastAPI and PostgreSQL"
schema_type: planning
status: published
owner: core-maintainer
purpose: "Record the initial architecture decision for the AMC Trainer app."
tags:
  - planning
  - architecture
  - decisions
component: Development-Tools
source: "/plan command generation"
---

> **Status**: Accepted
> **Date**: 2026-05-31
> **Supersedes**: None

## TL;DR

We will build a server-backed app (FastAPI + PostgreSQL via async SQLAlchemy) that stores
problems as structured records and grades submissions on the server, replacing the
prototype's single static HTML file with embedded content and `localStorage`.

## Context

### Problem

The prototype (`tmp/amc10-trainer.html`) is a single 4.6MB HTML file: KaTeX, problem images
(base64 PNG), answer keys, and app logic all inline, with state in `localStorage`. The
agreed v1 goals are persistent cross-device progress for a small private group, multi-user
accounts, and a content model that scales past hand-edited megabytes. None of these are
reachable without a server and a real datastore.

### Constraints

- **Technical**: `pyproject.toml` already pins FastAPI, Starlette, async SQLAlchemy, and
  Pydantic v2; `src/amc/` ships config, exceptions, security, and correlation middleware.
  Python 3.12. Quality gates: Ruff, BasedPyright strict, >= 80% coverage.
- **Business**: Solo developer; bounded audience (~1-30 users); self-hosted.

### Significance

This sets the data boundary and persistence model. Reversing it later (for example, moving
from static-local to server-backed after building features) means rewriting the data layer,
the grading path, and the storage of every attempt. Choosing now is cheap; changing later
is not.

## Decision

**We will use a FastAPI backend with PostgreSQL (async SQLAlchemy) serving a JSON API to a
browser frontend, because it is the only option that meets the persistence, multi-user, and
content-scaling goals while matching the existing scaffolding.**

### Rationale

Server-side storage is the single hard requirement behind cross-device progress and
multi-user tracking. Grading on the server is a free win it unlocks: answer keys never ship
to the client (the prototype leaks the full key in page source). Storing problems as rows
plus asset files removes the 4.6MB embed and makes adding a paper a seed/import step.

## Options Considered

### Option 1: Server-backed FastAPI + PostgreSQL ✓

**Pros**:

- ✅ Cross-device, multi-user persistence (the core v1 goal).
- ✅ Server-side grading keeps answer keys off the client.
- ✅ Uses the dependencies and middleware already in the repo.

**Cons**:

- ❌ Requires hosting, a database, migrations, and auth.

### Option 2: Static SPA (keep the prototype shape)

**Pros**:

- ✅ Fastest path; no backend to operate.

**Cons**:

- ❌ `localStorage` cannot sync across devices or separate users: fails the primary goal.
- ❌ Answer keys remain exposed in client code.

### Option 3: Hybrid (static now, backend later)

Defers the database but ships persistence-blind features first, then forces a data-layer
rewrite once the server arrives. Rejected: it spends effort on throwaway local state and
delays the one capability the user ranked highest.

## Consequences

### Positive

- ✅ Progress persists per user and is visible to a coach: directly serves the audience.
- ✅ Content scales: a new paper is a database/seed change, not an HTML edit.
- ✅ Integrity: grading and keys live server-side.

### Trade-offs

- ⚠️ Operational surface (DB, migrations, deploy): mitigate with Docker Compose for local
  Postgres and Alembic migrations from Phase 0.
- ⚠️ SQLite is tempting for simplicity; we choose PostgreSQL for JSON columns and concurrent
  writers, accepting the heavier local setup.

### Technical Debt

- Assets are served from the app filesystem in v1; object storage/CDN is deferred until
  group size or asset volume justifies it.

## Implementation

### Components Affected

1. **`src/amc/api/`**: new routers for auth, exams, diagnostics, attempts, progress.
2. **`src/amc/` (new `db/`, `models/`, `services/`)**: SQLAlchemy models, session wiring,
   grading and recommendation services.
3. **`alembic/`**: migrations (new).
4. **Frontend**: a React 19 SPA fetching from the API instead of the prototype's inline
   `DATA`; framework choice and same-origin topology are recorded in
   [ADR-002](./adr-002-frontend-framework.md).

### Testing Strategy

- Unit: grading and recommendation services at 100% (financial-grade correctness paths).
- Integration: API endpoints against a test Postgres (transaction rollback per test).

## Validation

### Success Criteria

- [ ] An attempt submitted on one device is retrievable on another for the same account.
- [ ] No correct-answer field appears in any pre-submission API response or page source.
- [ ] Adding one new AMC paper requires no change to application HTML/JS.

### Review Schedule

- Initial: end of Phase 1 (persistence proven end-to-end).
- Ongoing: revisit if audience approaches public scale.

## Related

- [Project Vision](../project-vision.md): scope and audience that drive this decision.
- [Tech Spec](../tech-spec.md): data model, endpoints, and auth that implement it.
