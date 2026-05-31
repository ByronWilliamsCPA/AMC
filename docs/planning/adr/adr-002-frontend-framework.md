---
title: "ADR-002: React 19 SPA for the Frontend"
schema_type: planning
status: published
owner: core-maintainer
purpose: "Record the frontend framework decision for the AMC Trainer app."
tags:
  - planning
  - architecture
  - decisions
  - frontend
component: Development-Tools
source: "/project-planning assumption reconciliation"
---

> **Status**: Accepted
> **Date**: 2026-05-31
> **Refines**: [ADR-001](./adr-001-initial-architecture.md)

## TL;DR

We will build the frontend as the React 19 + TypeScript + Vite SPA the template already
committed under `frontend/`, consuming a generated typed OpenAPI client, rather than the
vanilla-JS + KaTeX static page the early drafts assumed. SPA and API are served same-origin
behind a reverse proxy, so the `SameSite=Lax` session cookie avoids CORS-with-credentials.

## Context

### Problem

Two frontend architectures contradicted each other:

1. Early planning drafts (PVS, tech spec) described a **vanilla-JS + KaTeX**, server-served
   static HTML page refactored from the prototype, with same-origin cookie auth.
2. The cookiecutter template had already committed a working **React 19 + TypeScript + Vite
   SPA** under `frontend/` (axios, a generated OpenAPI client via `@hey-api/openapi-ts`,
   vitest, eslint/prettier, Dockerfile, `nginx.conf`).

A frontend framework is expensive to reverse once feature code accretes, so this had to be
resolved before Phase 1.

### Constraints

- **Technical**: `frontend/` ships React 19, Vite 6, TypeScript 5.7, vitest, and OpenAPI
  client generation; the backend exposes `/openapi.json`. Quality gates apply to both stacks.
- **Business**: Solo developer; bounded audience (~1-30 users); self-hosted.

### Significance

The UI is a **stateful application**, not a document: timer, 25 answers, flags, palette
navigation, review mode, live diagnostic self-mark recompute, and a dashboard. The framework
choice sets how that state is managed for the project's life.

## Decision

**We will use the scaffolded React 19 + TypeScript + Vite SPA as the frontend, consuming a
generated typed OpenAPI client, because it is the better long-term fit for a growing
stateful UI and it keeps the project on the cookiecutter template's golden path.**

### Rationale

The case for vanilla JS (ship fast, no toolchain) is short-term; the case for React is
long-term:

- **State scales with features, not discipline.** The runner only grows (the PVS defers
  adaptive practice, spaced repetition, per-topic drills). Hand-rolled DOM code degrades as
  that lands; a component model absorbs it.
- **Type-safe API contract.** The generated client makes frontend types track the Pydantic
  schemas, catching drift at build time on an app whose hard requirements are "no answer-key
  leakage" and "scores match the prototype."
- **Template alignment.** Deleting the scaffold to hand-serve static HTML would make every
  future `cruft update` fight the project, a recurring tax on a solo developer.
- **Testability.** vitest + testing-library is already wired, so the runner is
  component-testable rather than DOM-scraped.

The "4.6MB single-file" pain was about base64-embedded content and `localStorage`, solved by
ADR-001, not by the frontend framework. Dropping the framework would not have addressed it.

## Options Considered

### Option 1: React 19 + TypeScript + Vite SPA (the existing scaffold) ✓

- ✅ Component state fits the stateful runner and scales with features.
- ✅ Generated typed client guards the correctness-critical API boundary.
- ✅ Reuses the working scaffold and the template's golden path.
- ❌ Node build toolchain in CI (mostly paid); separate origin needs a reverse proxy.

### Option 2: Vanilla JS + KaTeX, server-served static HTML

- ✅ No build step; same-origin cookie auth "just works"; incremental prototype port.
- ❌ Hand-managed state degrades as features accrete; no type-safe API contract; fights the
  template scaffold and future `cruft` updates.

## Consequences

### Positive

- ✅ Maintainable home for growing UI state; compile-time protection on the submit/grade
  contract; stays on the template's supported full-stack shape.

### Trade-offs

- ⚠️ **Same-origin requirement.** The SPA and API must sit behind one origin so the
  `HTTP-only` `Secure` `SameSite=Lax` cookie works without CORS-with-credentials. Mitigation:
  a reverse proxy (`frontend/nginx.conf`) routes `/api/*` to FastAPI and `/*` to the SPA.
- ⚠️ **Asset exposure temptation.** Do not let nginx serve `assets/` (problem images)
  unauthenticated; serve them through the authenticated API so content stays behind auth.
- ⚠️ A second toolchain (node) to patch alongside Python.

## Implementation

Build the UI in `frontend/` (runner, diagnostics, progress as React components on the
generated client); front SPA and API on one origin via `frontend/nginx.conf`; test runner
state with vitest; regenerate the OpenAPI client in CI and fail on drift.

## Validation

### Success Criteria

- [ ] The session cookie authenticates API calls with no CORS-credentials relaxation.
- [ ] No `correct_answer` reaches the client before submission (unchanged from ADR-001).
- [ ] Regenerating the OpenAPI client produces no diff in CI.

### Review Schedule

- Initial: end of Phase 1, once the React runner persists attempts end-to-end.
- Ongoing: revisit only if team or scope changes enough to question the toolchain.

## Related

- [ADR-001](./adr-001-initial-architecture.md): server-backed architecture this refines.
- [Project Vision](../project-vision.md): scope and the now-resolved frontend assumption.
- [Tech Spec](../tech-spec.md): frontend stack, deployment topology, and auth.
