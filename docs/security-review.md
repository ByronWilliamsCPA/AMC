---
title: "Security Review (Phase 3.4)"
schema_type: common
status: published
owner: core-maintainer
purpose: "Phase 3.4 security review of authentication, authorization, answer-key non-exposure, and the same-origin cookie posture, with findings and applied remediations."
tags:
  - security
  - compliance
---

This review audits the AMC backend against the security acceptance criteria in
[tech-spec.md](planning/tech-spec.md) section "Security". Scope: authentication
and sessions, role-based authorization, answer-key non-exposure, input
validation, the same-origin cookie/CORS posture, and logging hygiene. The
review combined a specialist automated pass with manual verification of every
finding against the source.

Outcome: no critical or high findings. The core posture (Argon2id password
hashing, opaque signed server-side sessions, RBAC on every protected route, and
structurally key-free read schemas) passed. Four lower-severity gaps were found
and **all have been remediated** in this branch.

## Findings and remediations

| ID | Severity | Issue | Status |
|----|----------|-------|--------|
| F-1 | Medium | Login short-circuited the Argon2 verify for unknown emails, leaking account existence through response timing; an inline comment wrongly claimed this was mitigated. | Fixed |
| F-2 | Low | CORS middleware set `allow_credentials=True` with an empty origin list and wildcard `allow_headers` (non-conformant when combined). | Fixed |
| F-3 | Low | `/health/ready` returned the raw database exception (which can carry the DSN/credentials) to unauthenticated callers. | Fixed |
| F-4 | Low | The in-process login rate limiter is bypassed across multiple app replicas; the production compose defaulted to 2. | Fixed |

### F-1: Login timing / user enumeration (Medium)

`POST /auth/login` computed `user is not None and verify_password(...)`, so an
unknown email skipped the ~100 ms Argon2 work entirely while a known email paid
it, a timing oracle for account enumeration that the per-email rate limiter does
not cover. Remediation ([auth.py](https://github.com/ByronWilliamsCPA/AMC/blob/main/src/amc/api/auth.py)):
verify against a module-level dummy hash when the email is unknown, so both
paths cost the same work, and the misleading comment was removed. Tests assert
the unknown-email and wrong-password responses are identical in status and
message.

### F-2: CORS credentials posture (Low)

`add_security_middleware` emitted `Access-Control-Allow-Credentials: true`
unconditionally, even with no configured origins, and paired it with
`allow_headers=["*"]` (disallowed with credentials per the Fetch standard). No
active exploit existed given the same-origin reverse-proxy topology, but the
configuration was misleading. Remediation: credentials are now enabled only when
explicit origins are configured, and headers are listed explicitly. Recorded as
template feedback, since the middleware originates from the project template.

### F-3: Health-endpoint information disclosure (Low)

The unauthenticated readiness probe serialized the raw driver exception. A
connection failure could surface the database DSN, including a password, in the
response body. Remediation: the endpoint now returns a generic
`"database connectivity check failed"` message and logs the full error
server-side at warning level.

### F-4: Rate limiter across replicas (Low)

`LoginRateLimiter` keeps per-email counters in process memory. With the
production compose default of two replicas behind the proxy, an attacker
alternating replicas doubled the effective attempt budget. Remediation: the
production replica default is now 1, with a comment that scaling past one
replica requires moving rate-limit state to a shared store first.

## Verified controls (pass)

- **Passwords**: Argon2id via `argon2-cffi`; no bcrypt/MD5/SHA-1 for security use.
- **Sessions**: opaque server-side `Session` rows; cookie is `HttpOnly`, `Secure`,
  `SameSite=Lax`, and signed (itsdangerous, SHA-256 HMAC). Expiry and `revoked`
  checked per request; logout revokes; production boot guard enforces a strong
  `SESSION_SECRET` and the `Secure` flag.
- **Invites**: 256-bit `secrets.token_urlsafe` tokens; only the SHA-256 hash is
  stored; lookup is by hash; redemption is one-time.
- **Authorization**: every protected route depends on `CurrentUser` /
  `StaffUser`; `authorize_view_user` confines students to their own data while
  allowing staff to read any student's.
- **Answer-key non-exposure**: pre-submission read schemas
  ([exam.py](https://github.com/ByronWilliamsCPA/AMC/blob/main/src/amc/schemas/exam.py),
  [diagnostic.py](https://github.com/ByronWilliamsCPA/AMC/blob/main/src/amc/schemas/diagnostic.py))
  have no field that can carry a key; endpoints construct key-free objects
  explicitly. `password_hash` is never serialized.
- **Injection**: Pydantic validation at boundaries; SQLAlchemy parameterized
  queries throughout; no string-built SQL.
- **Logging**: no passwords, session tokens, raw invite tokens, or full answer
  keys are logged.

## Residual risk and follow-ups

- **Dependency vulnerabilities**: GitHub reports open Dependabot alerts on the
  repository (tracked separately under the known-vulnerabilities policy). This
  review covered application code, not the dependency tree; triage those before
  release.
- **Live verification**: cookie flags and the production boot guard are verified
  by unit/integration tests; confirm them once more against a running production
  build during the deploy drill.
