---
title: "AMC - Technical Specification"
schema_type: planning
status: active
owner: core-maintainer
purpose: "Document the technical architecture and implementation details."
tags:
  - planning
  - architecture
component: Development-Tools
source: "/plan command generation"
---

> **Status**: Draft | **Version**: 1.0 | **Updated**: 2026-05-31

## TL;DR

A FastAPI backend serves a JSON API over PostgreSQL (async SQLAlchemy) to a React 19 SPA,
served same-origin behind a reverse proxy so session-cookie auth works without CORS
relaxation. The SPA renders math with KaTeX and consumes a typed client generated from the
API's OpenAPI schema. Problems live as structured rows with assets as files; grading and the
placement recommendation run server-side; a small private group authenticates with session
cookies. See [ADR-001](./adr/adr-001-initial-architecture.md) and
[ADR-002](./adr/adr-002-frontend-framework.md).

## Technology Stack

### Core

- **Language**: Python 3.12 (repo supports >=3.10,<3.15)
- **Package Manager**: UV
- **Framework**: FastAPI >= 0.120, Starlette >= 0.49, Uvicorn[standard] >= 0.23
- **Validation**: Pydantic v2 + pydantic-settings (already configured)

### Code Quality

- **Linter / Formatter**: Ruff (88 chars, PyStrict-aligned)
- **Type Checker**: BasedPyright (strict)
- **Testing**: pytest + pytest-asyncio + coverage (>= 80%)

### Data Layer

- **Database**: PostgreSQL 16, see [ADR-001](./adr/adr-001-initial-architecture.md)
- **ORM**: SQLAlchemy 2.0 (asyncio) with asyncpg driver
- **Migrations**: Alembic
- **Assets**: problem images on the app filesystem under `assets/` (object storage deferred)

### Frontend

- **Framework**: React 19 + TypeScript 5.7, built with Vite 6 (scaffold under `frontend/`)
- **API client**: axios with a typed client generated from `/openapi.json`
  (`@hey-api/openapi-ts`); regenerated in CI and checked for drift
- **Math**: KaTeX (auto-render), proven in the prototype
- **Tooling**: vitest + testing-library, eslint, prettier
- **Auth transport**: HTTP-only `Secure` `SameSite=Lax` session cookie; works because the
  SPA and API are served **same-origin** behind a reverse proxy (see Deployment Topology),
  so no CORS-with-credentials relaxation is needed. See
  [ADR-002](./adr/adr-002-frontend-framework.md).

### Infrastructure

- **CI/CD**: GitHub Actions (CI, security, docs, publish already scaffolded); frontend lint,
  typecheck, vitest, and OpenAPI-client drift check added.
- **Container**: Docker + docker-compose (FastAPI app + Postgres + a reverse proxy serving
  the built SPA) for local and deploy.

### Deployment Topology

```text
            ┌──────────────── reverse proxy (one origin) ────────────────┐
client ──►  │  /api/*  ─► FastAPI (uvicorn)      /*  ─► built React SPA   │
            └────────────────────────────────────────────────────────────┘
```

Routing both under one origin keeps the session cookie same-origin and `SameSite=Lax` valid.
The existing `frontend/nginx.conf` is the proxy configuration. Problem images under `assets/`
are served through the authenticated API, never as unauthenticated static files, so content
stays behind auth.

## Architecture

### Pattern

Modular monolith: one FastAPI app, layered into routers -> services -> repositories ->
models. See [ADR-001](./adr/adr-001-initial-architecture.md).

### Component Diagram

```text
┌──────────────────────────────────────────────────────┐
│              Browser: React 19 SPA (Vite)             │
│        test runner · diagnostics · progress · KaTeX   │
└───────────────────────────┬──────────────────────────┘
                            │ JSON over HTTPS (cookie auth)
                            │ same-origin via reverse proxy
                            │ ( /api/* -> app, /* -> SPA )
┌───────────────────────────▼──────────────────────────┐
│                    FastAPI application                │
├───────────┬───────────┬───────────┬──────────────────┤
│   auth    │  catalog  │ attempts  │  progress/recommend│
│  router   │  router   │  router   │     router         │
├───────────┴───────────┴───────────┴──────────────────┤
│  services: grading · recommendation · auth/session     │
│  middleware: correlation · security (existing)         │
├────────────────────────────────────────────────────────┤
│         repositories (async SQLAlchemy)                │
└───────────────────────────┬──────────────────────────┘
                            ▼
                ┌───────────────────────┐   ┌──────────────┐
                │   PostgreSQL 16        │   │ assets/ files│
                └───────────────────────┘   └──────────────┘
```

### Component Responsibilities

| Component | Purpose | Key Functions |
|-----------|---------|---------------|
| auth router | Login, logout, current user | `login`, `logout`, `me` |
| catalog router | Serve exams, problems, diagnostics (no keys) | `list_exams`, `get_exam`, `list_diagnostics` |
| attempts router | Accept submissions, return graded results | `submit_exam`, `submit_diagnostic`, `list_attempts` |
| progress router | History + synthesized recommendation | `get_progress` |
| grading service | Score exams (6-point/count, voided) and diagnostics | `score_exam`, `grade_diagnostic` |
| recommendation service | Ladder walk + AMC gates from prototype | `synthesize` |
| repositories | Async DB access per aggregate | CRUD per entity |

### Grading & Scoring Rules

Ported verbatim from the prototype's `scoreTest` to avoid silent correctness drift; there is
**no partial credit**:

- **`score_mode == "sixpoint"`** (AMC 10/12): `score = correct*6 + blank*1.5`;
  `max = scored_problems * 6`, where `scored_problems = num_problems - len(voided)`.
- **`score_mode == "count"`** (AMC 8): `score = correct`; `max = scored_problems`.
- **Voided problems** (1-based numbers in `Exam.voided`) are excluded from `correct`,
  `wrong`, `blank`, and `max`. The runner shows them as "void" in review.
- Answer keys come from the **AoPS Wiki** (`Exam.source_url`); Phase 3 verifies every seeded
  key against that source before release.
- Diagnostics: auto-graded items use the prototype's `checkAuto` parsing (integers,
  fractions like `5/7`, mixed numbers, `2^7`); symbolic items are `manual` and self-marked.

## Data Model

### Core Entities

```python
class User:
    id: UUID
    email: str            # unique; login identifier
    display_name: str
    role: str             # "student" | "coach" | "admin"
    password_hash: str    # Argon2 (see Security)
    created_at: datetime

class Invite:              # one-time onboarding token
    id: UUID
    token_hash: str        # SHA-256 of the random token; raw token e-mailed/shared once
    email: str             # who it is for
    role: str              # role granted on redemption
    created_by: UUID       # FK -> User (coach/admin)
    expires_at: datetime
    redeemed_at: datetime | None

class Session:             # server-side session record (cookie carries id only)
    id: UUID               # opaque session id; set in signed HTTP-only cookie
    user_id: UUID          # FK -> User
    created_at: datetime
    expires_at: datetime   # sliding 14-day expiry
    revoked: bool

class Exam:                # one AMC paper
    id: UUID
    contest: str           # "AMC 8" | "AMC 10" | "AMC 12"
    year: int
    variant: str           # "A" | "B"
    duration_sec: int
    score_mode: str        # "sixpoint" | "count"
    num_problems: int
    voided: list[int]      # 1-based problem numbers excluded from scoring
    source_url: str | None

class Problem:
    id: UUID
    exam_id: UUID          # FK -> Exam
    number: int            # 1..num_problems
    render_mode: str       # "latex" | "image"
    body_latex: str | None
    image_path: str | None # relative path under assets/
    choices: dict | None   # latex mode: [{"L": "A", "html": "..."}]
    correct_answer: str    # "A".."E"  (never serialized pre-submission)
    solution_url: str | None

class DiagnosticInstrument:
    id: str                # "pa1-pre", "algB-post", ...
    course: str            # "Prealgebra 1", ...
    kind: str              # "Are You Ready?" | "Do You Know?"
    role: str              # "AYR" | "DYK"
    ladder: dict           # prev/self/next labels
    grading: dict          # mode + thresholds (need / fundNeeded / psNeeded)
    instructions: str

class DiagnosticItem:
    id: UUID
    instrument_id: str     # FK -> DiagnosticInstrument
    section_title: str
    label: str
    prompt: str            # may contain LaTeX
    answer: str            # canonical answer (never sent pre-submission)
    group: str | None      # "fund" | "ps" (for fundps grading)
    manual: bool           # symbolic answers are self-marked

class TestAttempt:
    id: UUID
    user_id: UUID          # FK -> User
    exam_id: UUID          # FK -> Exam
    started_at: datetime
    submitted_at: datetime | None
    answers: list[str | None]
    flags: list[bool]
    time_used_sec: int
    score: float
    correct: int
    wrong: int
    blank: int
    max_score: float

class DiagnosticAttempt:
    id: UUID
    user_id: UUID          # FK -> User
    instrument_id: str     # FK -> DiagnosticInstrument
    submitted_at: datetime
    responses: dict        # item_id -> raw input
    marks: dict            # item_id -> bool (self-marked items)
    passed: bool
    verdict: str           # "win" | "mid" | "low"
    summary: str           # score line + recommendation message
    elapsed_sec: int
```

### Relationships

- User one-to-many TestAttempt; User one-to-many DiagnosticAttempt
- Exam one-to-many Problem; DiagnosticInstrument one-to-many DiagnosticItem
- Recommendation is computed on read from a user's attempts (not stored).

## API Specification

### Endpoints

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| POST | /api/v1/invites | Create a one-time invite (coach/admin) | Yes |
| GET | /api/v1/invites/{token} | Validate an invite token | No |
| POST | /api/v1/auth/register | Redeem invite, set password, create account | No |
| POST | /api/v1/auth/login | Start a session | No |
| POST | /api/v1/auth/logout | End (revoke) the session | Yes |
| GET | /api/v1/auth/me | Current user | Yes |
| GET | /api/v1/exams | List papers (filter by contest) | Yes |
| GET | /api/v1/exams/{id} | Problems without correct answers | Yes |
| POST | /api/v1/exams/{id}/attempts | Submit answers, get graded result | Yes |
| GET | /api/v1/diagnostics | List instruments | Yes |
| GET | /api/v1/diagnostics/{id} | Items without answers | Yes |
| POST | /api/v1/diagnostics/{id}/attempts | Submit + self-marks, get verdict | Yes |
| GET | /api/v1/attempts | This user's attempt history | Yes |
| GET | /api/v1/progress | History + synthesized recommendation | Yes |
| GET | /api/v1/users/{id}/progress | A student's progress (coach/admin) | Yes |

### Request/Response Format

```json
// POST /api/v1/exams/{id}/attempts  (request)
{ "answers": ["C", null, "B", "..."], "flags": [false], "time_used_sec": 4120 }

// response (graded; correct answers revealed only now)
{
  "score": 102.0, "max_score": 138, "correct": 17, "wrong": 6, "blank": 2,
  "review": [{ "n": 1, "your": "C", "correct": "C", "ok": true,
               "solution_url": "https://..." }]
}
```

## Security

### Authentication

Email + password; passwords hashed with **Argon2** via `argon2-cffi` (avoid bcrypt per the
FIPS guidance in `CLAUDE.md`).

**Session mechanism (decided here, not deferred):** opaque **server-side sessions** backed
by the `Session` table. On login the server creates a `Session` row and sets its `id` in a
signed, HTTP-only, `Secure`, `SameSite=Lax` cookie. Each request loads the row, checks
`expires_at` and `revoked`, and slides expiry (14-day window). Logout sets `revoked = true`.
Server-side sessions (not JWTs) are chosen so a coach can revoke a student's access instantly
and so no token state lives in the browser; the cost is one indexed DB read per request,
negligible at this scale.

**Onboarding flow (invite-only, no open signup):** a coach/admin calls `POST /invites` to
mint a one-time token (the raw token is shared with the student once; only its hash is
stored). The student opens the invite link, `GET /invites/{token}` validates it, and
`POST /auth/register` redeems the unexpired token, sets the Argon2 password, creates the
`User`, and marks the invite redeemed.

### Authorization

Role-based: `student` sees only their own data; `coach`/`admin` may read any student's
progress. Enforced in a FastAPI dependency on every protected route.

### Data Protection

- **At Rest**: DB on an encrypted volume; password hashes only (never plaintext).
- **In Transit**: TLS terminated at the reverse proxy.
- **Sensitive Data**: `Problem.correct_answer` and `DiagnosticItem.answer` are never placed
  in any pre-submission response (server-side grading), closing the prototype's key leak.
- Input validated by Pydantic; parameterized queries via SQLAlchemy.

## Error Handling

### Strategy

Fail fast with the centralized hierarchy in `src/amc/core/exceptions.py`; a FastAPI
exception handler maps each to an HTTP status and a structured body. Correlation IDs from the
existing middleware tie logs to responses.

### Error Codes

| Code | Meaning | User Action |
|------|---------|-------------|
| 400 | ValidationError (bad answer payload) | Fix input and resubmit |
| 401 | AuthenticationError (no/expired session) | Log in again |
| 403 | AuthorizationError (other student's data) | None; not permitted |
| 404 | ResourceNotFoundError (exam/attempt) | Check the identifier |
| 409 | BusinessLogicError (double submit) | Reload latest result |

### Logging

Structured JSON via `src/amc/utils/logging.py`, levels DEBUG-ERROR, correlation IDs
included. Never log password hashes, session tokens, or full answer keys.

## Performance Requirements

| Metric | Target | Measurement |
|--------|--------|-------------|
| Catalog/attempt API p95 | < 200 ms | server timing under test load |
| Exam page interactive | < 2 s | Lighthouse on a seeded paper |
| Grade-and-store submit | < 300 ms | endpoint benchmark |
| Test suite | < 30 s | full pytest run with coverage |

## Testing Strategy

### Coverage Target

- Minimum 80% line / 70% branch overall.
- Grading and recommendation services: 100% (correctness-critical).

### Test Types

- **Unit (backend)**: scoring (6-point, count, voided), `synthesize` ladder/gate logic,
  auth deps.
- **Unit (frontend)**: vitest + testing-library for runner state (timer countdown/auto-submit,
  flag toggles, palette navigation) and diagnostic self-mark recompute.
- **Integration**: each API route against a test Postgres with per-test rollback.
- **Contract**: regenerate the OpenAPI client in CI; fail on uncommitted drift.
- **E2E**: take an exam, submit, see it persist and reappear on a second session.

## Related Documents

- [Project Vision](./project-vision.md)
- [ADR-001: Server-Backed Architecture](./adr/adr-001-initial-architecture.md)
- [ADR-002: React 19 SPA Frontend](./adr/adr-002-frontend-framework.md)
- [Development Roadmap](./roadmap.md)
