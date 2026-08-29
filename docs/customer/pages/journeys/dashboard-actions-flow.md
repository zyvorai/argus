# Flow test

## Purpose

Multi-step user journey (English or step DSL) with optional login/session, video, and Playwright `trace.zip`.

## When to use it

- Prove a critical path after deploy (signup, checkout, create VM, …)
- Capture a single end-to-end video for stakeholders
- Reuse a session from [Auth & session](../api/dashboard-actions-auth.md)

## How to get there

- Surface: `/dashboard/actions/flow`
- UI: Mission Control → **Journeys** → **Flow test** (or ⌘K → “Flow”)

## Operate from the console (UX)

1. Enter the app URL and either English (“go to products, click Schedule Demo, assert contact”) or one step per line.
2. Optional: login user/password, reuse a saved session file, pick browser / device / throttle.
3. Keep **record video** on, then **🎬 Run journey**.
4. Watch the live job panel; download video + trace when finished.

### Step language (excerpt)

`goto`, `click`, `hover`, `fill`, `select`, `upload`, `download`, `dialog`, `iframe`, `drag`, `press`, `clock`, `wait`, `wait until`, `assert`, `assert url`, `assert api`, `assert aria`, `assert not`, `assert count`, `assert value`.

CLI equivalent: `argus flow run <url> --steps file`.


5. **Empty / fail:** Check health, auth, and domain dependencies.
6. **Success:** Live data loads; mutations complete without error toasts.

## Related pages

- [HAR record / replay](dashboard-actions-har.md)
- [Import codegen](dashboard-actions-import-codegen.md)
- [Auth & session](../api/dashboard-actions-auth.md)
- [Getting Started](../../getting-started.md)
- [Page index](../../PAGE_INDEX.md)
