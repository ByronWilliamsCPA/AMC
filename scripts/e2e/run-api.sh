#!/usr/bin/env bash
# Boot the AMC API for the Playwright e2e harness against a throwaway SQLite DB
# seeded from the synthetic content/e2e_seed.json. Invoked by playwright.config
# as a webServer; Playwright waits on http://localhost:8000/health/live.
set -euo pipefail

# Run from the repo root regardless of caller cwd.
cd "$(dirname "$0")/../.."

export DATABASE_URL="sqlite+aiosqlite:///./.e2e/amc_e2e.db"
# Bootstrap password for the out-of-band coach; matches global-setup.ts.
export AMC_ADMIN_PASSWORD="${AMC_ADMIN_PASSWORD:-e2e-coach-pw-12345}"

# Fresh database each run.
rm -rf .e2e
mkdir -p .e2e

# 1. Schema.
uv run alembic upgrade head

# 2. Seed exams + diagnostic from the synthetic file (same file for both args).
uv run python -m amc.seed --amc content/e2e_seed.json --diag content/e2e_seed.json

# 3. Coach for the invite bootstrap. create_admin refuses to overwrite, so a
#    repeat run on a reused DB is tolerated.
uv run python -m amc.create_admin \
  --email coach@example.test --name "E2E Coach" --role coach || true

# 4. Serve. exec so signals reach uvicorn for clean Playwright shutdown.
exec uv run uvicorn amc.main:app --host 127.0.0.1 --port 8000
