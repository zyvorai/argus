# Tutorial 11 — E2E flow tests & route sweeps

The rest of the agent generates one test *per page* or *per requirement*. A **flow test** is different: it drives a **multi-step user journey** — log in → navigate → click through a wizard → fill fields → assert the outcome — as one continuous Playwright session, **recorded end-to-end as a single journey video**. This is the pattern real product QA lives on.

This tutorial covers flow tests and their companion, the **route sweep** (screenshot many routes at desktop + mobile and pixel-diff them against baselines).

Prerequisites: Tutorial 1 (install), and Playwright browsers installed (`make playwright` or `npx playwright install chromium`).

---

## 1. Your first flow, from the CLI

Create a step file — one step per line, no LLM needed:

```
# journey.flow
go to /
assert "HyperSDK"
click "Products"
assert /products
```

Run it against any site:

```bash
argus flow run https://zyvor.dev --steps journey.flow --video
```

You get per-step pass/fail on the console and, when `--video` is set, a `journey.webm` recorded from the very first navigation to the last assertion:

```
▶ step 1: goto /                     ✓
▶ step 2: assert "HyperSDK"          ✓
▶ step 3: click "Products"           ✓
▶ step 4: assert /products           ✓
4/4 steps passed · journey.webm (1.3 MB)
```

### Plain English instead of steps

Skip the file and describe the journey:

```bash
argus flow run https://zyvor.dev \
  --describe "Go to the home page, click Products, then verify the Pro plan is visible"
```

When an LLM key is configured (`ANTHROPIC_API_KEY`) the description is parsed by the model (`prompts/flow.md`); otherwise a verb-pattern heuristic splits it into steps. Both produce the same step list the runner executes.

### Logging in first

```bash
argus flow run https://app.example.com --steps checkout.flow \
  --username qa@example.com --password 's3cret' --insecure
```

`--insecure` accepts self-signed certificates (sets `ZYVOR_IGNORE_HTTPS_ERRORS`). The runner does a best-effort login (finds an email/password field, submits) before the first step, so your steps start from an authenticated page.

---

## 2. The step language

| Step | Playwright it drives |
|------|----------------------|
| `go to <path>` / `goto` / `open` / `navigate` | `page.goto(base + path)` + wait for load |
| `click "<text>"` | `getByRole('button'/'link')` → `getByText` → CSS fallback |
| `hover "<text>"` | hover the matched control |
| `fill <field> = <value>` (`type`/`enter`) | `getByLabel` / `getByPlaceholder` / CSS `.fill(value)` |
| `select <field> = <option>` | `selectOption` by label or value |
| `upload <field> = <path>` | `setInputFiles` |
| `download "<text>" [to <path>]` | click + wait for download event |
| `dialog accept\|dismiss [text]` | arm next `dialog` handler before the click that opens it |
| `iframe <selector>` / `iframe off` | scope following steps to a frame (or clear) |
| `drag "<src>" to "<dst>"` | `dragTo` |
| `press <key>` | `page.keyboard.press(value)` — e.g. `press Enter` |
| `clock install\|set:ISO\|fastForward:ms` | `page.clock.*` time mocking |
| `wait [for] <selector\|ms>` | `waitForSelector` or `waitForTimeout` |
| `wait until "<text\|sel>" [Nms]` | poll until visible (eventual UI) |
| `assert "<text>"` / `assert /path` (`verify`/`expect`/`check`) | text visible, heading, or URL match |
| `assert url <path>` | URL must match |
| `assert api <substr> [= status]` | wait for a matching network response |
| `assert aria <sel> = <snapshot>` | aria-tree fragment must appear |
| `assert not "<text>"` / `assert no "<text>"` | text/element must **not** be visible (spinner gone, error absent) |
| `assert count <selector> = <n>` | exactly `n` elements match the CSS selector |
| `assert value <field> = <value>` | an input holds the expected value |

A bare line with no verb is treated as `assert "<that text>"`. A step **fails** not only on a Playwright error but also if a runtime error fires during it — the runner scans the page body for `Something went wrong`, `ReferenceError`, `is not defined`, and hooks `page.on('pageerror')`. That catches "the button clicked but the app threw" bugs a naive click test would miss.

The prose parser also detects negatives — "the spinner is **no longer** visible", "the error **should not** appear" become `assert_not` steps.

Import a Playwright codegen recording with `argus test import-codegen script.js` (or Mission Control's 📥 Import codegen card). Local headed recording: `npm run record-flow -- https://app.example.com out.flow.json`.

### Robustness

The runner is built to survive real apps and flaky servers:

- **Overlay dismissal** — before the first step (and after each navigation) it clicks past cookie banners and onboarding modals (Accept / Got it / Dismiss / Skip / Close / Escape) so they don't block the journey.
- **Navigation retry** — each `goto` (and the login navigation) retries up to 3× with backoff, surviving cold starts and server churn.

Every step also captures a screenshot, and the whole run is saved as one video (`context.recordVideo`, finalized with `page.video().saveAs()` after the context closes — ordering matters, Playwright only writes the file on context close).

### Trace — the time-travel debugger

By default the runner captures a **Playwright trace** (`trace.zip`) alongside the video. Download it from the result panel (🔍) or the CLI output and open it at [trace.playwright.dev](https://trace.playwright.dev) — you get a per-step timeline with the DOM snapshot, network log, and console at each moment. This is the fastest way to see *why* a step failed. Turn it off with `--no-trace` (CLI) for a lighter run.

---

## 3. Flow tests in Mission Control

Open the dashboard (Tutorial 10) and find the **🎬 Flow test** card:

1. Enter the base URL.
2. Paste an English journey **or** one step per line into the textarea (the parser auto-detects which).
3. Optionally set login user/pass, tick **self-signed TLS**, and toggle **record video**.
4. **Run journey.**

Steps stream live into the job panel (`✓ step 3: click "Products"`) with a running tally. When it finishes you get:

- a **step table** — order, action, pass/fail, and each step's screenshot,
- the **journey video embedded inline** (plays right in the page),
- the **HTML / PDF / Markdown / CSV** report download row (bundle under `reports/jobs/<ts>-flow/`) — Markdown also has a one-click **⧉ Copy MD** for pasting into a GitHub PR or Slack,
- **Rerun** to run the same journey again.

On Kubernetes the video and report persist on the PVC-backed `reports/`, so they survive pod restarts and show up in the **🎬 videos** panel and **⬇ all videos (zip)**.

---

## 4. Route sweep — visual coverage across many pages

The **🗺 Route sweep** card (and `argus vision route-sweep`) screenshots a list of routes at chosen viewports and, on later runs, diffs them against baselines.

```bash
# first run captures baselines
argus vision route-sweep https://zyvor.dev --routes "/,/products,/pricing" --mobile

# later runs diff against them; flags any route over the threshold
argus vision route-sweep https://zyvor.dev --routes "/,/products,/pricing" --mobile

# accept the new look as the baseline
argus vision route-sweep https://zyvor.dev --routes "/,/products,/pricing" --update-baselines

# don't type routes at all — crawl the site and sweep whatever it finds
argus vision route-sweep https://zyvor.dev --auto --max-pages 20 --mobile
```

Tick **auto-discover (crawl)** in the 🗺 card to do the same from the dashboard. Every sweep also writes a downloadable **HTML / PDF / Markdown / CSV** report (route × viewport matrix with thumbnails), same as flow tests.

- Desktop is **1440×900**, mobile is **375×812**.
- Dynamic content that flakes pixel diffs — `canvas`, charts (`.recharts-*`), clocks, timestamps, skeletons — is **masked**, and CSS animations are disabled.
- The sweep waits for skeletons/`.animate-pulse` to disappear rather than `networkidle` (live apps never go idle).
- Diffs use the same Pillow differ as visual regression (Tutorial 6); routes over `VISUAL_MAX_DIFF_RATIO` are flagged.
- Baselines live under `reports/artifacts/route-baselines/` (PVC-backed).

The result is a route × viewport matrix with each cell's diff % and thumbnail — a fast way to catch layout drift across an entire site after a deploy.

---

## 5. When to reach for which

- **Flow test** — a specific critical path must keep working: signup, checkout, the create-resource wizard. One journey, asserted step by step, with a video you can hand to whoever needs to see the failure.
- **Route sweep** — broad "did anything shift visually?" coverage across many pages after a CSS/library change.
- **Crawl (`🌐 Test any site`)** — discovery: generate and run a check on *every* page without naming them.

Use flow tests for the paths you can't afford to break, and route sweeps + crawl for breadth.

---

## 6. Run them on a loop

Both flow tests and route sweeps are **schedulable**. Fill in the 🎬 or 🗺 card, then in the **Schedules** panel pick *flow test* or *route sweep* and an interval — the schedule reuses whatever you entered in the card. A critical signup journey every 15 minutes, a full-site route sweep nightly: the console becomes a monitor, and each run lands in QA history with its video/trace/report.

---

## 7. Serving securely (HTTPS)

The dashboard is served over plain HTTP by default. For anything reachable beyond localhost, serve it over TLS:

```bash
# self-signed cert, auto-generated under ~/.zyvor-argus/tls
argus serve --port 8090 --tls

# or bring your own
argus serve --port 8090 --tls-cert /path/cert.pem --tls-key /path/key.pem
```

Over HTTPS the session cookie is marked **Secure**. The deploy script takes `--tls` to do this on a host (`deploy-remote.sh <host> <user> --service --tls`). Login is also **rate-limited** — 8 failed attempts from an IP within 5 minutes triggers a 5-minute lockout — so a default password isn't a free brute-force target. Still, change `DASHBOARD_PASSWORD` from the default for any real deployment.

**Target credentials never echo back.** When a flow or crawl logs in to the *site under test*, the login password you pass is used to drive the session but is redacted (`***`) everywhere it would otherwise surface — the job-status API, run history, and the live panel. It is never returned to a dashboard reader in cleartext.

---

## Configuration

Relevant environment variables (see [configuration](../configuration.md)):

| Variable | Effect |
|----------|--------|
| `ZYVOR_VIDEO` | `on` records journey video by default |
| `ZYVOR_IGNORE_HTTPS_ERRORS` | accept self-signed certs (set by `--insecure`) |
| `ZYVOR_NO_SANDBOX` | Chromium `--no-sandbox` (needed as root / in-cluster) |
| `ZYVOR_PW_WORKERS` | Playwright worker cap (default 2 in-cluster to bound memory) |
| `VISUAL_MAX_DIFF_RATIO` | route-sweep pixel-diff pass threshold |
| `VISUAL_SETTLE_MS` | extra settle time per route before screenshot |
| `ANTHROPIC_API_KEY` | enables LLM journey parsing (heuristic otherwise) |
| `DASHBOARD_PASSWORD` | enables dashboard login (rate-limited); change from the default |
| `DASHBOARD_SECRET` | explicit session-signing secret (else derived from credentials) |

The flow trace is on by default; pass `--no-trace` to the CLI to skip it. Serve over HTTPS with `argus serve --tls` (self-signed) — see section 7.

## Related

- [Tutorial 19 — Test a CRM (UI-first)](19-crm-golden-paths.md) — apply the same flow + session pattern to HubSpot, Pipedrive, Zoho, Salesforce
- [Tutorial 12 — API, Auth, Live-data](12-api-auth-realtime.md)
- [Tutorial 13 — zyvor.dev recording](13-test-zyvor-dev-recording.md)
