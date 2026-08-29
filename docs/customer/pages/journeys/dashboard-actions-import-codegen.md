# Import codegen

## Purpose

Paste Playwright codegen JS/TS and convert it into Zyvor Argus flow steps (optionally run immediately).

## When to use it

- You already recorded a journey with `playwright codegen`
- You want flow DSL without rewriting clicks by hand

## How to get there

- Surface: `/dashboard/actions/import-codegen`
- UI: Mission Control → **Journeys** → **Import codegen**

## Operate from the console (UX)

1. Paste codegen output (`page.goto`, `getByRole().click`, `fill`, …).
2. Optionally tick **run as flow** and provide the app URL.
3. Click **📥 Import** — inspect emitted steps; run if requested.
4. CLI: `argus test import-codegen script.js [--run --url …]`.
5. Local headed record alternative: `npm run record-flow -- <url> out.flow.json`.


5. **Empty / fail:** Check health, auth, and domain dependencies.
6. **Success:** Live data loads; mutations complete without error toasts.

## Related pages

- [Flow test](dashboard-actions-flow.md)
- [Getting Started](../../getting-started.md)
- [Page index](../../PAGE_INDEX.md)
