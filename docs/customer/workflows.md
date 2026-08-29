# Common workflows

## Smoke after a deploy

1. [Run tests](pages/pipeline/dashboard-actions-run-tests.md) → ▶ Smoke (or `argus test exec --grep @smoke`)
2. Check [Findings](pages/operations/dashboard-findings.md) and [QA Runs](pages/operations/dashboard-runs.md)

## Spec → tests → report

1. [Generate tests](pages/pipeline/dashboard-actions-generate.md) or CLI `argus test run --source local --spec …`
2. [Run tests](pages/pipeline/dashboard-actions-run-tests.md) → Full pipeline
3. Optional: enable autofix via `ENABLE_AUTOFIX` (see Admin basics)

## Record and replay a journey

1. [Flow test](pages/journeys/dashboard-actions-flow.md) — English or step DSL, record video
2. Or [Import codegen](pages/journeys/dashboard-actions-import-codegen.md) from Playwright codegen
3. [HAR record / replay](pages/journeys/dashboard-actions-har.md) when you need offline network fixtures

**Public demo:** [Test zyvor.dev](test-zyvor-dev.md) — watch the committed journey `.webm`, then re-run smoke / flow / HAR against `https://zyvor.dev`.

## API, auth, and live data

1. [Auth & session](pages/api/dashboard-actions-auth.md) → save session file
2. [API contract](pages/api/dashboard-actions-api-contract.md) against OpenAPI
3. [Live data](pages/api/dashboard-actions-realtime.md) for WebSocket / SSE
4. Reuse the session on [Flow test](pages/journeys/dashboard-actions-flow.md)

## Visual confidence

1. [Route sweep](pages/visual/dashboard-actions-route-sweep.md) or [Visual regression](pages/visual/dashboard-actions-regression.md)
2. [Compare URLs](pages/visual/dashboard-actions-compare.md) for staging vs prod
3. [Web Vitals](pages/quality/dashboard-actions-vitals.md) for LCP / CLS / INP

## Continuous monitoring

1. Configure the card once (e.g. audit URL or flow steps)
2. [Schedules](pages/operations/dashboard-schedules.md) → pick kind + interval

## Related

- [Getting Started](getting-started.md)
- [Using the Dashboard](using-the-dashboard.md)
- [Page index](PAGE_INDEX.md)

## Operate from the console (UX)

1. Open this route from the nav or command palette and wait for live API data.
2. Use filters/search when present; drill into a row for detail.
3. For mutating actions: confirm role gates and impact before applying.
4. **Empty / fail:** Check service health, auth, and that required CRDs/backends for this domain are installed.
5. **Success:** Live data loads; created/updated objects appear without error toasts.

