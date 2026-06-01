---
title: "Authentik / OIDC SSO (optional, not yet enabled)"
schema_type: common
status: draft
owner: core-maintainer
purpose: "Ready-to-enable path for single sign-on against a locally hosted Authentik instance."
tags:
  - architecture
  - security
  - integration
---

AMC Trainer ships with **built-in authentication** — invite-only onboarding,
Argon2 password hashing, and server-side sessions behind an HTTP-only cookie
(see [`tech-spec.md`](../planning/tech-spec.md) §Security). That is the active,
tested scheme.

This document is the **ready-to-enable** path for single sign-on against a
locally hosted [Authentik](https://goauthentik.io/). The decision on record is to
keep built-in auth for now and adopt Authentik later, mapping **Authentik groups
to application roles**.

## Why backend-for-frontend (BFF)

When SSO is adopted, the recommended design keeps everything that already works
and changes only *how a user proves their identity*:

```text
Browser ──► FastAPI /auth/oidc/login ──► Authentik (login)
        ◄── redirect with ?code= ──────────────┘
Browser ──► FastAPI /auth/oidc/callback
                    │  exchanges code for tokens (server-side)
                    │  reads the `groups` claim → role_from_groups()
                    │  creates the SAME Session row as password login
                    └─ sets the existing amc_session cookie
```

- **Tokens never reach the browser.** FastAPI does the Authorization Code
  exchange; the SPA only ever sees the existing HTTP-only session cookie. This
  is the most secure option for a SPA + API and avoids the XSS token-theft
  surface of holding tokens in the browser.
- **Nothing downstream changes.** The `Session` table, the RBAC dependency,
  `GET /auth/me`, and the entire frontend `AuthContext` are identical — they
  already derive everything from the session, not from how login happened.
- The only removal is the built-in password login (`POST /auth/login`) and the
  invite/register flow, which Authentik's enrollment replaces.

## What already exists in the codebase

- **Config** (`src/amc/core/config.py`): `oidc_enabled` (default `False`) plus
  `oidc_issuer`, `oidc_client_id`, `oidc_client_secret`, `oidc_redirect_url`,
  `oidc_scopes`, `oidc_staff_group`, `oidc_admin_group`.
- **Roles mapping** (`src/amc/core/oidc.py`): `role_from_groups()` maps the
  `groups` claim to `admin` / `coach` / `student` (admin > coach > student),
  unit-tested.
- **Stub routes** (`src/amc/api/oidc.py`): `/api/v1/auth/oidc/login` and
  `/callback`, mounted **only** when `oidc_enabled` is true. They return 501
  until the flow is implemented, so pointing Authentik at the app before it is
  wired up fails loudly instead of silently.

## Enabling it (future work)

1. **Authentik**: create an OAuth2/OpenID provider and an application for AMC
   Trainer. Set the redirect URI to `https://<host>/api/v1/auth/oidc/callback`.
   Add a `groups` scope/claim. Create groups (e.g. `amc-staff`, `amc-admin`) and
   assign members.
2. **App config** (environment, never committed secrets):

   ```bash
   AMC_OIDC_ENABLED=true
   AMC_OIDC_ISSUER=https://authentik.example.lan/application/o/amc/
   AMC_OIDC_CLIENT_ID=...
   AMC_OIDC_CLIENT_SECRET=...            # from the environment/secret store
   AMC_OIDC_REDIRECT_URL=https://amc.example.lan/api/v1/auth/oidc/callback
   AMC_OIDC_STAFF_GROUP=amc-staff
   AMC_OIDC_ADMIN_GROUP=amc-admin
   ```

3. **Implement the flow** in `src/amc/api/oidc.py` (replacing the stubs). A small
   library such as `authlib` handles discovery, the code exchange, and JWT
   validation. On a valid callback:
   - upsert a `User` keyed by the `sub`/`email` claim,
   - set its role via `role_from_groups(claims["groups"])`,
   - create a `Session` (reuse `SessionRepository`) and set the cookie exactly
     as `amc.api.auth.login` does.
4. **Frontend**: replace the login form's submit with a redirect to
   `/api/v1/auth/oidc/login`. The rest of the SPA (the `/auth/me`-derived
   `AuthContext`, route guards, logout) is unchanged.

## Roles

With `groups -> roles` (the chosen mapping), Authentik owns who is staff:

| Authentik group        | App role  |
| ---------------------- | --------- |
| `AMC_OIDC_ADMIN_GROUP` | `admin`   |
| `AMC_OIDC_STAFF_GROUP` | `coach`   |
| (any other member)     | `student` |

If you later prefer the app to own roles/onboarding instead, keep the invite
flow and ignore the group claim — the mapping function is the only thing to swap.
