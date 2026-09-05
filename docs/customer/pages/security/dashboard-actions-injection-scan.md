# Injection scan

## Purpose

Systematic SQLi / reflected-XSS / path-traversal probes — requires exploit engagement and ZYVOR_DAST_SCAN_ENABLED.

## When to use it

- Open this card when the job matches the purpose above
- Prefer **Mission Control** (`/dashboard`) and the **⌘K** command palette if you are unsure where to start
- Confirm a live security engagement and any required opt-in flags (see purpose) before starting

## How to get there

- Surface: `/dashboard/actions/injection-scan`
- UI: Mission Control → **Security** → **Injection scan** (side rail panel, or ⌘K / Ctrl-K Search)
- CLI: `argus guard injection-scan`

## Operate from the console (UX)

1. Open `/dashboard` (sign in at `/login` when `DASHBOARD_PASSWORD` is set).
2. Create or select an authorized **Security engagement**, fill the card fields for **Injection scan**, then start the action and watch the live job panel (✓/✗ chips, Stop, download log).
3. After success, check **Findings**, **QA Runs**, and any report links the card produces.

If the card stays idle or errors, hit `GET /health`, confirm the webhook/dashboard process is up (`argus serve`), and re-check env from [.env.example](../../../../.env.example). See also [Network-attack / DAST gaps](../../../security-network-attack-gaps.md).

## Related pages

- [Security engagements](dashboard-actions-security-engagements.md)
- [Getting Started](../../getting-started.md)
- [Using the Dashboard](../../using-the-dashboard.md)
- [Mission Control](../overview/dashboard.md)
- [Page index](../../PAGE_INDEX.md)
