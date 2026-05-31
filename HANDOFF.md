# AMC Trainer — Backend Handoff

This document describes the backend implemented in this environment, what remains
for the local team, and how to run and finish it. It complements the plan in
[`docs/planning/PROJECT-PLAN.md`](docs/planning/PROJECT-PLAN.md).

## What is done

The Phase 0 foundation and the backend half of Phase 1 / Phase 2 are implemented,
tested, and green. The server-side logic that the spec calls correctness-critical
(grading, diagnostics, recommendation) is complete with 100% unit coverage.

| Area | Status | Notes |
|------|--------|-------|
| FastAPI app factory + middleware | ✅ | `src/amc/main.py`; correlation + security wired; prod safety guard |
| Async SQLAlchemy + session DI | ✅ | `src/amc/core/database.py` |
| ORM models (9 entities) | ✅ | `src/amc/models/` |
| Alembic migrations | ✅ | `migrations/`; verified `upgrade`/`downgrade`/`check` on PostgreSQL 16 |
| Grading service (`score_exam`) | ✅ | 100% coverage; six-point/count/voided per CONSTANTS.md §1 |
| Diagnostic grading + auto-grader | ✅ | 100% coverage; CONSTANTS.md §8 tolerances and normalisation |
| Recommendation (`synthesize`) | ✅ | 100% coverage; ladder walk + algA special + AMC gates, CONSTANTS.md §5–7 |
| Auth: Argon2, sessions, invites, RBAC | ✅ | `src/amc/core/security.py`, `src/amc/api/auth.py`, `deps.py` |
| Login rate limiting | ✅ | `src/amc/services/auth.py` (credential-stuffing mitigation) |
| Catalog / attempts / progress API | ✅ | Answer keys never serialized pre-submission (structural) |
| Content seed loader | ✅ | `src/amc/seed.py`; idempotent; seeds the real diagnostic bundle |
| Same-origin reverse proxy | ✅ | `frontend/nginx.conf` proxies `/api/` and `/health/` to the app |
| Test suite | ✅ | 208 tests, 82% overall coverage, services at 100% |
| Ruff / BasedPyright / Bandit | ✅ | Zero ruff errors; zero pyright errors in `src/`; no Bandit findings |

The full API surface (matches `docs/planning/tech-spec.md`):

```
GET  /health/{live,ready,startup}
POST /api/v1/auth/login | logout | register
GET  /api/v1/auth/me
GET  /api/v1/auth/invites/{token}        # validate an invite (public)
POST /api/v1/invites                      # mint an invite (coach/admin)
GET  /api/v1/exams | /api/v1/exams/{id}
POST /api/v1/exams/{id}/attempts
GET  /api/v1/diagnostics | /api/v1/diagnostics/{id}
POST /api/v1/diagnostics/{id}/attempts
GET  /api/v1/progress
GET  /api/v1/users/{id}/progress          # self, or any user for staff
```

## What remains (local team)

1. **Deliver `content/amc_data.json`** — the ~4 MB file with the nine AMC papers
   (225 problems, base64 images). It could not be transferred into this
   environment (only inline text reaches the container; large attachments do
   not). Everything that consumes it is ready:
   - `content/validate_content.py` validates it against the contract.
   - `python -m amc.seed` loads it (it already tolerates the file being absent
     and seeds diagnostics only).
   - `src/amc/services/grading.py` grades it; the model and API serve it.

2. **AMC score gates in the recommendation** — `synthesize` accepts an
   `amc_gates` list but the progress endpoint passes `[]` until the diagnostic
   `catalog` (which carries the `gate: "amc"` / `min` rows) is seeded into a
   dedicated table or read from the seeded instruments. The ladder walk and the
   conjunction-warning logic are implemented and tested; wire the gates when the
   catalog is seeded. See `src/amc/api/progress.py:_build_progress`.

3. **Frontend (React SPA)** — the `frontend/` scaffold exists; the exam runner,
   diagnostics, and progress components are Phase 1/2 frontend work. The backend
   exposes an OpenAPI schema at `/openapi.json` and
   `scripts/generate-client.sh` regenerates the typed client.

4. **Backup/restore drill** — Phase 0 deliverable 0.6; document a `pg_dump` +
   tested restore in the deploy guide.

5. **Phase 3 polish** — answer-key verification against the AoPS Wiki, a11y /
   mobile pass, Lighthouse, and the security review.

## Running it

### Backend (local, SQLite)

```bash
uv sync --extra api --extra dev
uv run uvicorn amc.main:app --reload      # http://127.0.0.1:8000/docs
```

By default the app uses a local SQLite file (`amc.db`). For a quick start without
migrations, the schema can be created from the models; for anything real, use
Alembic (below).

### Backend (PostgreSQL + migrations)

```bash
export AMC_DATABASE_URL='postgresql+asyncpg://amc:password@localhost:5432/amc'
uv run alembic upgrade head                # creates all tables
python -m amc.seed --diag content/diag_data.json \
    --amc content/amc_data.json            # once amc_data.json is delivered
```

### Full stack (Docker)

```bash
docker compose up -d                       # app + Postgres + nginx (same-origin)
```

`frontend/nginx.conf` proxies `/api/` and `/health/` to the FastAPI app so the
`SameSite=Lax` session cookie works without CORS relaxation.

### Bootstrapping the first admin

Onboarding is invite-only and minting an invite requires a coach/admin, so the
first admin must be created out-of-band (a short script or a REPL using
`amc.core.security.hash_password` and `amc.repositories.users.UserRepository`).
A `create-admin` management command is a good first addition for the local team.

## Configuration

Settings load from environment variables (`AMC_` prefix; `DATABASE_URL`,
`SESSION_SECRET`, `ENVIRONMENT` also accepted unprefixed). Key ones:

| Variable | Default | Notes |
|----------|---------|-------|
| `AMC_DATABASE_URL` | `sqlite+aiosqlite:///./amc.db` | async driver auto-applied |
| `AMC_SESSION_SECRET` | dev sentinel | **must** be set in production (boot guard) |
| `AMC_SESSION_COOKIE_SECURE` | `true` | set `false` for local HTTP |
| `AMC_ENVIRONMENT` | `development` | `production` enables HTTPS redirect + secret guard |
| `AMC_LOGIN_MAX_ATTEMPTS` / `_WINDOW_SECONDS` | 5 / 300 | login rate limit |

## Quality gates

```bash
uv run pytest --cov=src/amc --cov-fail-under=80
uv run ruff check . && uv run ruff format --check .
uv run basedpyright src/
uv run bandit -c pyproject.toml -r src/
```

## Notes for reviewers

- **Answer-key non-exposure is structural.** The read schemas in `src/amc/schemas/`
  have no field that could hold a key, so a pre-submission response cannot leak
  `correct_answer` / `answer` / `v` / `accept`. An integration test asserts this.
- **Two pre-existing middleware bugs were fixed** while wiring the app: a runtime
  crash in `SecurityHeadersMiddleware` (`MutableHeaders` has no `pop`) and the
  `call_next` typing in both middlewares. See the `test(api)` commit.
- **Template feedback** for issues that originate from the cookiecutter template
  (a dead CLI test stub, a `.gitignore` rule that swallowed `src/amc/models/`)
  is recorded in `docs/template_feedback.md` per project policy.
