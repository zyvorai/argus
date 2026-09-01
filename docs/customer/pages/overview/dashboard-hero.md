# Hero status

## Purpose

Cluster/app health banner with pods, replicas, last QA run, pass rate, next schedule, and knowledge (Ask Zyra) stat tile.

## When to use it

- First screen after sign-in — one glance at overall health
- Stat sub-lines explain offline cluster, empty run history, or knowledge install state

## How to get there

- Surface: `/dashboard/hero` · hash `#overview`
- UI: Mission Control → **Overview** panel (default landing)

## Operate from the console (UX)

1. Read the status lamp and headline (ALL SYSTEMS GO / DEGRADED / SYSTEMS DOWN / CLUSTER OFFLINE).
2. Scan stat tiles — pods/replicas show **No cluster connected** when kube is unavailable (not an error on a laptop).
3. **Knowledge** tile reflects Ask Zyra status; hover for install hints when offline.

Auto-refreshes every 5 s; press `r` to refresh now.

## Related pages

- [Using the Dashboard](../../using-the-dashboard.md)
- [Mission Control](../overview/dashboard.md)
- [Ask Zyra](../console/dashboard-ask.md)
- [Page index](../../PAGE_INDEX.md)
