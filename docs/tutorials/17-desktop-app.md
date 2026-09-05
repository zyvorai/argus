# Tutorial 17 — Desktop app (macOS)

A native window around Mission Control — `argus serve`'s dashboard, without a browser tab.

**Prerequisites:** [Tutorial 1](01-getting-started.md), [Tutorial 10](10-mission-control-dashboard.md).

---

## 1. What this is (and isn't)

`desktop/` is a thin [Tauri 2](https://tauri.app) shell: it spawns
`argus serve` as a child process and points a native window at
`http://127.0.0.1:<port>/dashboard`. It is **not** a reimplementation —
every dashboard action (triggering a run, viewing reports, managing
schedules) goes through the exact same FastAPI server, job queue, CSRF
protection, and rate limiting as `argus serve` does normally. Closing
the window kills the spawned server; nothing is left running in the
background.

It also does **not** bundle a self-contained Python+Node+Playwright
runtime — it wraps your existing local install (the repo's own `.venv`, or
a `pip`-installed `argus` on `PATH`). See `ROADMAP.md`'s "Desktop app
v2" entry for why that's a deliberate v1 boundary, not an oversight.

## 2. Requirements

- Node.js 20+, Rust (`rustup` or Homebrew), Xcode Command Line Tools
- A working `argus` install — `make install` from the repo root gives
  you `.venv/bin/argus`, auto-detected in dev
- Node/Playwright (also from `make install`) — only needed to actually
  *run* jobs from the dashboard, not to view it

## 3. Run it

```bash
npm install          # from the repo root — sets up the desktop/ workspace too
npm run desktop
# or
make desktop-dev
```

A window opens with a brief loading screen, then hands off to the real
dashboard once `argus serve` is ready (usually under a second).

## 4. Build a standalone app

```bash
make desktop-build
```

Produces an **unsigned** `Zyvor Argus.app`/`.dmg` under
`desktop/src-tauri/target/release/bundle/macos/` — open it directly, no
`npm run desktop` needed. Unsigned means macOS Gatekeeper will warn on
first launch (right-click → Open). For a signed + notarized build (needs
an Apple Developer account), see `desktop/README.md`'s "Code signing &
notarization" section and `make desktop-build-signed`.

## 5. Pointing it at a different `argus`

If you have multiple Python environments, or the auto-detected binary
isn't the one you want, override it via **⌘,** (or **Zyvor Argus →
Settings…** in the menu bar) rather than hand-editing anything — enter the
full path to the binary and Save. Takes effect on the next restart.

## 5b. Remote Mission Control (lab / team)

A true single-binary bundle with embedded Chromium is impractical (hundreds
of MB of browser binaries). For lab or shared runners, set **Settings →
Remote URL** to an existing Mission Control base URL (e.g.
`http://212.8.248.187:30080`). The shell skips spawning local `argus serve`
and opens that dashboard — Playwright/Chromium stay on the remote host.
Leave Remote URL blank to keep the default local spawn.

## 6. What's different from viewing it in a browser

- The Kubernetes pods/workloads panel is hidden — it's always "cluster
  unavailable" for a locally-wrapped app with no cluster of its own, so
  it's just clutter here (`ZYVOR_DESKTOP_MODE=true`, set automatically by
  the app; everything else in the dashboard is identical).
- Otherwise nothing — same server, same job queue, same CSRF/rate-limiting.

## 7. Security notes

- The spawned server binds to `127.0.0.1` only — opening the app never
  exposes the dashboard to your LAN, even though `argus serve`'s own
  CLI default is `0.0.0.0`.
- A random free port is chosen per launch (not a fixed 8080), so a second
  instance or a port conflict doesn't just fail.
- `DASHBOARD_PASSWORD` is unset by default (matches `argus serve`'s own
  default) — the desktop app assumes a single local user. Set it in your
  `.env` if you want the login/CSRF/rate-limiting path exercised even
  locally.

**See also:** [`desktop/README.md`](../../desktop/README.md) for the
Rust-side implementation notes, and [Tutorial 10](10-mission-control-dashboard.md)
for everything the dashboard itself can do.
