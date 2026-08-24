# Login

## Purpose

Mission Control `DASHBOARD_PASSWORD` login gate; Argus Enterprise uses Keycloak/OIDC with demo accounts `demo`/`demo` and `ssouser`/`Sso@321` (see the Enterprise SSO chapter in this manual).

For **Argus Enterprise** (Watchfloor) full setup steps, open [Enterprise SSO / OIDC](../../enterprise-sso.md) — that product does not use `DASHBOARD_PASSWORD`.

## When to use it

- You opened `/dashboard` and were redirected to `/login`
- You need to confirm Mission Control auth before running cards that read
  cluster logs or artifacts
- Prefer **Mission Control** (`/dashboard`) and the **⌘K** command palette if
  you are unsure where to start

## How to get there

- Surface: `/login`
- UI: open `/dashboard` when auth is enabled (redirect), or go directly to `/login`

## What you can do

### Mission Control (community)

1. Ensure `DASHBOARD_PASSWORD` (and optional `DASHBOARD_USER`, default `admin`) is set.
2. Open `/login`, enter username + password (lab defaults are often
   `admin` / `Admin@321` — rotate for anything exposed).
3. Optional: check **Remember me** for a longer session (30 days vs 12 h).
4. After success you land on `/dashboard`. `/health` and `/webhook/github` stay open.

### Argus Enterprise (Watchfloor)

1. Claim the fresh install with the one-time setup token from app logs.
2. On the login screen, choose the SSO / Keycloak provider (or the local
   email/password form if local auth is enabled).
3. Demo accounts after a default Keycloak install:
   - `demo` / `demo`
   - `ssouser` / `Sso@321`
4. Verify with `scripts/test-login.sh https://argus.example.com demo demo`.

Full steps (Helm, BYO OIDC, local auth, troubleshooting):
[Enterprise SSO / OIDC](../../enterprise-sso.md).

If Mission Control login fails, hit `GET /health`, confirm `argus serve` is up,
and re-check env from [.env.example](../../../../.env.example).

## Related pages

- [Getting Started](../../getting-started.md)
- [Admin basics](../../admin-basics.md)
- [Enterprise SSO / OIDC](../../enterprise-sso.md)
- [Using the Dashboard](../../using-the-dashboard.md)
- [Mission Control](../overview/dashboard.md)
- [Page index](../../PAGE_INDEX.md)
