# Mission Control

## Purpose

Live Mission Control console — grouped side rail (Console / Testing / Security / Operations), dark theme, status hero, workloads, pods, category action panels, requirements, schedules, findings, and QA run history.

## When to use it

- Your starting point for every QA action and cluster health view
- Prefer the **side rail** or **⌘K / Search** if you are unsure where to start
- Confirm `ZYVOR_BASE_URL`, dashboard auth, and that Playwright browsers are installed if runs fail immediately

## How to get there

- Surface: `/dashboard`
- UI: sign in at `/login` when auth is enabled, then use the **side rail** or `#overview` hash URL

## Operate from the console (UX)

1. Open `/dashboard` (sign in at `/login` when `DASHBOARD_PASSWORD` is set).
2. **Overview** — hero stat tiles, workloads, pods, live job terminal.
3. **Testing panels** — Pipeline, Visual, Quality, Journeys, API, Probes, Requirements — run jobs one at a time with a live Terminal-style log.
4. **Ask Zyra** — optional citation-first knowledge Q&A ([Tutorial 14](../../../tutorials/14-ask-zyra-knowledge.md)).
5. **Security testing** — engagements, recon, SCA, DB assert, chaos, sandboxed exploit tiers.
6. **Runs & schedules** — schedules, findings, run history, videos, test health.
7. **⌘K** or header **Search** — command palette to jump anywhere.

Use the **theme toggle** (moon/sun) for light mode; **Collapse** on the rail for icons-only.

If the console stays idle or errors, hit `GET /health`, confirm `argus serve` (or systemd `argus.service`) is up, and re-check env from [.env.example](../../../../.env.example).

## Related pages

- [Getting Started](../../getting-started.md)
- [Using the Dashboard](../../using-the-dashboard.md)
- [Ask Zyra](../console/dashboard-ask.md)
- [Page index](../../PAGE_INDEX.md)
