# HAR record / replay

## Purpose

Record a HAR while browsing routes, or replay the UI against a captured HAR (offline / deterministic network).

## When to use it

- Freeze API responses for flaky backends
- Diff UI behavior with vs without live network
- Share a network fixture with the team (`ZYVOR_HAR_PATH`)

## How to get there

- Surface: `/dashboard/actions/har`
- UI: Mission Control → **Journeys** → **HAR record / replay**

## Operate from the console (UX)

1. **Record** — set mode `record`, enter URL + routes (`/`, `/pricing`, …). HAR path can auto-generate.
2. **Replay** — set mode `replay`, point at the HAR file, optional expect-text, optional “allow missing routes”.
3. Click **📼 Run** and review the live log.
4. CLI: `argus api har-replay <url> --mode record|replay --har out.har`.


5. **Empty / fail:** Check health, auth, and domain dependencies.
6. **Success:** Live data loads; mutations complete without error toasts.

## Related pages

- [Flow test](dashboard-actions-flow.md)
- [Route sweep](../visual/dashboard-actions-route-sweep.md)
- [Getting Started](../../getting-started.md)
- [Page index](../../PAGE_INDEX.md)
