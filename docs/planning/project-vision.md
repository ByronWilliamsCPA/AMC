---
title: "AMC - Project Vision & Scope"
schema_type: planning
status: active
owner: core-maintainer
purpose: "Document the project vision, scope, and success criteria."
tags:
  - planning
  - scope
component: Strategy
source: "/plan command generation"
---

> **Status**: Active | **Version**: 1.0 | **Updated**: 2026-05-31

## TL;DR

AMC Trainer is a web app that lets a coach and a small set of students take timed AMC
8/10/12 practice contests and AoPS placement diagnostics, then synthesizes both signals
into a recommended starting course. v1 promotes a working single-file prototype into a
FastAPI-backed app so progress persists across devices for a known group of users.

## Problem Statement

### Pain Point

A working prototype (`tmp/amc10-trainer.html`) already proves the concept, but it is a
single 4.6MB HTML file that stores all state in `localStorage`. Three concrete problems
block real use:

1. **Progress is trapped on one device.** A student who practices on a laptop cannot see
   results on a tablet; clearing browser data erases every attempt.
2. **One hardcoded user.** The prototype is built "for Bayden" with no concept of separate
   students, so a coach cannot track more than one learner.
3. **Content does not scale.** Problems are embedded as base64 PNGs inside the HTML, which
   is why the file is 4.6MB; adding contests means hand-editing a megabyte-scale document.

### Target Users

- **Primary**: A math coach (admin) managing a **small, known group** (roughly 1-30
  students) preparing for AMC contests.
- **Secondary**: The students themselves, taking timed tests and diagnostics on whatever
  device is handy.
- **Context**: Self-paced practice at home plus coach review between sessions. Bounded,
  invite-based membership, not public signup.

### Success Metrics

- Cross-device continuity: % of attempts visible on a second device: 0% (localStorage) -> 100%.
- Multi-user support: distinct tracked students: 1 (hardcoded) -> up to 30.
- Content onboarding effort: time to add one new contest paper: hours of hand-editing a
  4.6MB file -> < 15 minutes via a seed/import workflow.
- Answer-key integrity: correct answers exposed in page source before submission:
  yes -> no (server-side grading).

## Solution Overview

### Core Value

Turn two practice signals (a timed AMC score and AoPS course diagnostics) into one durable,
multi-device, coach-visible recommendation for where each student should start.

### Key Capabilities (MVP)

1. **Accounts for a private group**: Invite-based login so each student has their own
   persistent record and a coach can see all of them. Solves the single-user limit.
2. **Timed AMC test runner with server-side grading**: Take AMC 8/10/12 papers with a
   timer, flagging, and palette navigation; the server grades on submit and stores the
   result. Solves device lock-in and answer-key leakage.
3. **Placement diagnostics + recommendation engine**: The 10 AoPS instruments
   ("Are You Ready?" / "Do You Know?") with auto and self-marked grading, plus the
   ladder-walking synthesis that recommends a starting course.
4. **Progress dashboard**: Per-student history of contest scores and diagnostics with the
   combined placement read, persisted server-side.

## Scope Definition

### In Scope (MVP)

- ✅ AMC 8, AMC 10, and AMC 12 timed practice tests (the prototype's nine seeded papers plus
  an import path for more): each paper is takeable, graded server-side, and stored.
- ✅ The 10 AoPS placement diagnostics with both auto-graded and self-marked items.
- ✅ Recommendation/synthesis engine reproducing the prototype's ladder logic and AMC gates.
- ✅ Invite-based accounts with student and coach roles; coach can view student progress.
- ✅ Persistent, cross-device storage of every test and diagnostic attempt.
- ✅ A content model that stores problems as structured records with assets as files, not
  base64 embedded in HTML.

### Out of Scope

- ❌ Public self-service signup, billing, or marketing site: audience is a bounded group.
- ❌ Authoring problems inside the app (admin content UI): v1 uses seed/import scripts.
- ❌ Auto-grading symbolic answers (radicals, polynomials): keep the prototype's manual
  self-mark for those items.
- 🔄 Adaptive practice, spaced repetition, per-topic drills: deferred to a later phase.
- 🔄 Native mobile apps: v1 is a responsive web app only.
- 🔄 Object-storage/CDN for assets: v1 serves assets from the app; revisit if it grows.

## Constraints

### Technical

- **Platform**: Responsive web app: a React SPA and the FastAPI backend served same-origin
  behind a reverse proxy (see [ADR-002](./adr/adr-002-frontend-framework.md)).
- **Language**: Python 3.12 (repo targets >=3.10,<3.15); TypeScript 5.7 on the frontend.
- **Stack**: FastAPI, SQLAlchemy (async), Pydantic v2 (backend); React 19 + Vite + a
  generated OpenAPI client (frontend). All present in `pyproject.toml` / `frontend/`.
- **Math rendering**: KaTeX, proven in the prototype.
- **Quality gates**: Ruff, BasedPyright strict, >= 80% coverage, signed conventional commits.
- **Performance**: catalog/attempt API p95 < 200ms; exam page interactive < 2s.

### Business

- **Timeline**: Target a usable v1 in roughly 7-9 weeks of part-time work (see roadmap).
- **Resources**: Solo developer with Claude Code assistance.
- **Legal**: AMC problems are MAA content released via the AoPS Wiki; keep the prototype's
  attribution and treat the app as a private, non-affiliated study aid.

## Assumptions

### Resolved (2026-05-31)

- [x] **Group <= ~30, invite-only, no open signup.** Drives server-side sessions and
  single-instance scaling; revisit only if the audience nears public scale (ADR-001 tripwire).
- [x] **Responsive web app is enough; no native mobile for v1.**
- [x] **Single self-hosted PostgreSQL.** Confirmed, conditioned on an automated backup plus a
  tested restore as a named deliverable ([roadmap](./roadmap.md) Phases 0/3), since durable
  progress is the core value.
- [x] **Redistributing AMC/AoPS content to a private group.** Accepted as a private,
  attributed, non-affiliated study aid; highest residual external risk. Mitigated by keeping
  content behind auth (never publicly crawlable), retaining MAA/AoPS attribution, and a
  takedown-response posture.
- [x] **Frontend framework: React 19 SPA over vanilla JS**
  ([ADR-002](./adr/adr-002-frontend-framework.md)).

### Still open

- [ ] Login rate-limiting suffices against credential stuffing (added to Phase 1 auth).

## Related Documents

- [Architecture Decisions](./adr/)
- [Technical Spec](./tech-spec.md)
- [Roadmap](./roadmap.md)
