---
title: "API documentation & monitoring"
schema_type: common
status: published
owner: core-maintainer
purpose: "Machine-readable API docs and a Newman-ready monitoring collection for the AMC Trainer."
tags:
  - api
  - api_reference
  - documentation
---

Machine-readable API docs and a Newman-ready monitoring collection.

| File | What it is |
|------|------------|
| `openapi.json` | The OpenAPI 3.1 schema (17 paths, 24 schemas). Import into Postman, Insomnia, or generate clients. |
| `amc.postman_collection.json` | A Postman v2.1 collection that monitors the core flow with assertions. |

Both are generated from the running app — never hand-edit them. A unit test
(`tests/unit/test_api_docs_export.py`) fails if they drift from the app.

## Regenerate

```bash
uv run python scripts/export_api_docs.py
```

This writes both files from `amc.main.create_app().openapi()`.

## Live docs

With the app running, interactive docs are at:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Raw schema: `http://127.0.0.1:8000/openapi.json`

## Monitoring with Newman

The collection chains `login -> me -> catalog -> progress -> logout` and asserts,
on each request: a 2xx status, response time under 800 ms, a JSON body, and — on
the catalog endpoints — that no answer key (`correct_answer` / `answer`) appears
in the pre-submission payload. Auth is session-cookie based; Newman's cookie jar
carries the `amc_session` cookie set by login through the rest of the run.

```bash
# Install Newman (Node)
npm install -g newman

# Run against an environment
newman run docs/api/amc.postman_collection.json \
    --env-var base_url=https://amc.example.com \
    --env-var email=coach@example.com \
    --env-var password='<password>'
```

Collection variables (override with `--env-var`):

| Variable | Default | Purpose |
|----------|---------|---------|
| `base_url` | `http://127.0.0.1:8000` | Target origin |
| `email` | `coach@example.com` | A real account to log in as |
| `password` | `change-me` | That account's password |

The monitoring account should be a low-privilege real user; the collection only
reads (it logs out at the end and creates nothing).

### Scheduled monitoring

`newman run` exits non-zero if any assertion fails, so it drops into any
scheduler or monitor:

- **Postman Monitors**: import the collection and schedule it in the Postman UI.
- **CI cron**: the `api-monitor` GitHub Actions job
  (`.github/workflows/api-monitor.yml`) runs Newman against a deployed
  environment on a schedule.
- **Reports**: add `-r cli,json,junit` for machine-readable output to wire into
  dashboards or alerting.
