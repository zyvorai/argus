# DB assert

## Purpose

Read-only SELECT-only assertion (row_count / cell_equals / column_values) against Postgres, MySQL, or SQLite — needs ZYVOR_DB_TESTING_ENABLED and an engagement; DSN is an env-var reference.

## When to use it

- Open this card when the job matches the purpose above
- Prefer **Mission Control** (`/dashboard`) and the **⌘K** command palette if you are unsure where to start
- Confirm `ZYVOR_BASE_URL`, dashboard auth, and that Playwright browsers are installed if runs fail immediately

## How to get there

- Surface: `/dashboard/actions/db-assert`
- UI: Mission Control → **Security** panel → **DB assert** (side rail, or ⌘K / Ctrl-K **Search**)

## What you can do

1. Open `/dashboard` (sign in at `/login` when `DASHBOARD_PASSWORD` is set).
2. Fill the card fields for **DB assert**, then start the action and watch the live job panel (✓/✗ chips, Stop, download log).
3. After success, check **Findings**, **QA Runs**, and any video / report links the card produces.
4. Turn recurring checks into a **Schedule** (5 min – 6 h) when you want continuous monitoring.

If the card stays idle or errors, hit `GET /health`, confirm the webhook/dashboard process is up (`argus serve`), and re-check env from [.env.example](../../../../.env.example).

## Related pages

- [Getting Started](../../getting-started.md)
- [Using the Dashboard](../../using-the-dashboard.md)
- [Mission Control](../overview/dashboard.md)
- [Page index](../../PAGE_INDEX.md)
