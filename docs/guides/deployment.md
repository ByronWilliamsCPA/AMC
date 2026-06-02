---
title: "Deployment & Operations"
schema_type: common
status: published
owner: core-maintainer
purpose: "Run the AMC stack end to end: configuration, migrations, content seeding, first-admin bootstrap, and a tested backup/restore drill."
tags:
  - guide
  - deployment
  - infrastructure
---

This guide takes a fresh machine to a running AMC stack and documents the
operational drills the deployment depends on. It covers the same-origin Docker
topology (FastAPI app, PostgreSQL, and the React SPA behind one reverse proxy),
database migrations, content seeding, bootstrapping the first staff account, and
a backup/restore procedure that has been tested, not just written.

## Prerequisites

- Docker and the Docker Compose plugin (`docker compose`, v2).
- A clone of this repository.
- The content bundle (see [Seeding content](#seeding-content)).

## Configuration

Settings load from environment variables (the `AMC_` prefix is optional for the
keys below). Copy `.env.example` to `.env` and set, at minimum:

| Variable | Purpose |
|----------|---------|
| `DB_PASSWORD` | PostgreSQL password for the `amc` role. |
| `DATABASE_URL` | Async connection string the app uses; must match `DB_PASSWORD`. |
| `AMC_SESSION_SECRET` | Session-cookie signing secret. **Required** in production; the app refuses to boot in production with the development sentinel. |
| `AMC_ENVIRONMENT` | `production` enables the HTTPS redirect and the secret guard. |

Never commit a real `.env`; it is gitignored.

## Bring up the stack

```bash
docker compose up -d
```

This starts the app, PostgreSQL 16 (`db` service, data on the `postgres-data`
volume), and the frontend behind the reverse proxy. `frontend/nginx.conf`
proxies `/api/` and `/health/` to the app so the `SameSite=Lax` session cookie
works without CORS relaxation.

## Apply migrations

The schema is managed by Alembic. Create every table with:

```bash
docker compose exec app uv run alembic upgrade head
```

`alembic upgrade head` is idempotent: it is safe to run on every deploy and
applies only outstanding migrations.

## Seeding content

The diagnostic bundle (`content/diag_data.json`) ships in the repository. The
AMC paper bundle (`content/amc_data.json`, roughly 4 MB of official problem
scans) is **kept local and is gitignored**: redistributing it through a public
repository is a licensing risk (see the planning risk register). Place the file
at `content/amc_data.json` on the deployment host before seeding; a fresh clone
will not contain it.

Validate the bundle against the content contract, then seed:

```bash
uv run python content/validate_content.py content/amc_data.json content/diag_data.json
docker compose exec app uv run python -m amc.seed \
  --amc content/amc_data.json --diag content/diag_data.json
```

Seeding is idempotent (rows are upserted), so re-running after a content update
will not duplicate exams, diagnostics, or catalog entries. If `amc_data.json` is
absent, seeding logs a warning and loads the diagnostics and catalog only.

## Bootstrap the first admin

Onboarding is invite-only and minting an invite requires an existing
coach or admin, so the first staff account must be created out of band:

```bash
docker compose exec app uv run python -m amc.create_admin \
  --email coach@example.com --name "Head Coach"
```

The command prompts for a password (with confirmation) and refuses to overwrite
an existing account. For non-interactive provisioning, supply the password via
the `AMC_ADMIN_PASSWORD` environment variable instead of a prompt. Once one staff
account exists, all further accounts are created through the in-app invite flow.

## Backup and restore

A single-instance database makes a tested restore the difference between a minor
incident and data loss. Two scripts wrap `pg_dump` / `psql` against the compose
`db` service; both accept `DB_SERVICE`, `DB_NAME`, and `DB_USER` overrides.

Create a compressed, timestamped dump (written under `backups/`, which is
gitignored):

```bash
scripts/backup.sh
```

Restore a dump. This overwrites the target database, so confirm the target
before running:

```bash
scripts/restore.sh backups/amc-20260602-120000Z.sql.gz
```

### Tested restore drill

Run this after any change to the schema or the backup tooling. It proves the
dump is replayable, not merely that a file was written:

1. Seed a known database (see [Seeding content](#seeding-content)) and note a
   verifiable fact, for example the exam count:

   ```bash
   docker compose exec db psql -U amc -d amc -c 'select count(*) from exams;'
   ```

2. Back it up: `backup_file=$(scripts/backup.sh)`.

3. Drop and recreate the schema (simulating loss), then restore:

   ```bash
   docker compose exec db psql -U amc -d amc -c 'drop schema public cascade; create schema public;'
   scripts/restore.sh "${backup_file}"
   ```

4. Re-read the same fact and confirm it matches the pre-backup value. A matching
   count means the restore reproduced the database; a mismatch fails the drill.

Record the date of the most recent successful drill in your operations log so a
stale backup path is caught before it is needed.
