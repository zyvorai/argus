# Tutorial 10 — Mission Control Dashboard

A live, self-refreshing operations console served by the webhook server. It shows Kubernetes pod health and logs, QA run history with trends, versioned **Requirements**, and category panels that run **25+** QA capabilities — every CLI command plus web-quality, API contracts, security, chaos, and performance checks — with live-streamed output and downloadable HTML/PDF/Markdown/CSV reports.

**UX:** Grouped **side rail** —
**Console** (Overview, Ask Zyra) ·
**Testing** (Pipeline, Visual, Quality, Journeys, API, Probes, Requirements) ·
**Security** (Security testing) ·
**Operations** (Runs & schedules) —
**dark theme by default** (charcoal surfaces, minimal blue `#2997ff` accent buttons), collapsible icons-only rail, global header with knowledge lamp + theme toggle + **Search** (⌘K palette), hash routing (`#overview`, `#ask`, `#pipeline`, `#requirements`, …), and a **macOS Terminal** live job console (Copy / Save / Stop) with syntax-colored logs. Reduced-motion aware.

**Watch:** Record a journey locally — [`docs/assets/zyvor-dev-demo.steps`](../assets/zyvor-dev-demo.steps) against https://zyvor.dev ([Tutorial 13](13-test-zyvor-dev-recording.md)).

**Prerequisites:** [Tutorial 1](01-getting-started.md). A Kubernetes cluster is optional — without one the pod panel shows **No cluster connected** and everything else still works. To practice against the public site with video + HAR, see [Tutorial 13](13-test-zyvor-dev-recording.md).

---

## 1. Open it locally

```bash
argus serve --port 8080
# then browse to:
open http://localhost:8080/dashboard
```

What you'll see on **Overview**:

- **Status hero** — one glanceable verdict with stat tiles for pods, replicas, last QA run, pass rate, next schedule, and knowledge (Ask Zyra):
  - `ALL SYSTEMS GO` — every pod healthy, last QA run green
  - `DEGRADED` — some pods unhealthy or the last QA run failed
  - `SYSTEMS DOWN` — every pod unhealthy
  - `CLUSTER OFFLINE` — no Kubernetes API reachable (normal on a laptop)
- **Workloads** — per-deployment replica readiness; per-cronjob schedule, last run, and countdown
- **Pods** — one card per pod: phase, ready containers, restart count, age, node, image, recent Warning events. **Click a pod** to open the log drawer (last 100 lines, live-refreshing; hover pauses refresh).
- **Live job** — when a card is running, the macOS Terminal panel streams here (also visible while you switch panels)

**Navigation:** use the **grouped side rail** to switch panels, or **⌘K** (Ctrl-K) / header **Search** for the command palette. **Theme toggle** (moon/sun) switches dark ↔ light; preference is saved in the browser. **Collapse** at the bottom of the rail for icons-only mode.

Keyboard: `r` refreshes immediately, `esc` closes the log drawer or palette. Everything auto-refreshes every 5 seconds (configurable in the footer).

## 2. Where run history comes from

Every pipeline run (`argus test run`, webhook-triggered runs) appends one JSON entry to `reports/history/` (kept to the most recent 200). Generate some data:

```bash
argus test run --source local
```

Refresh the dashboard — the run appears in the table and the sparkline.

## 3. Point it at a cluster

The Kubernetes panel activates automatically when an API is reachable, in this order:

1. **In-cluster** service account (when running as the K8s webhook Deployment)
2. **Local kubeconfig** (`~/.kube/config` or `KUBECONFIG`) — so `argus serve` on your laptop can watch any cluster you can

Configuration:

| Variable | Default | Purpose |
|----------|---------|---------|
| `DASHBOARD_NAMESPACE` | in-cluster namespace, else `default` | Namespace to inspect |
| `DASHBOARD_POD_SELECTOR` | *(all pods in namespace)* | Label selector, e.g. `app=zyvor-argus` |

Try it with a local cluster:

```bash
kind create cluster --name argus
DASHBOARD_NAMESPACE=kube-system argus serve --port 8080
```

## 4. Deploy on Kubernetes

The manifests already wire this up: `kubernetes/rbac.yaml` grants the `argus` service account read-only access (pods, logs, events, deployments, cronjobs) and the webhook Deployment uses it.

```bash
make k8s-validate
make k8s-apply
```

**Access is deliberately not exposed through the ingress** — the dashboard can read pod logs, which don't belong on the public internet. Use a port-forward:

```bash
kubectl port-forward svc/argus-webhook 8080:80
open http://localhost:8080/dashboard
```

If you do want it on the ingress, add an authenticated path — see [`kubernetes/README.md`](../../kubernetes/README.md#dashboard-optional-ingress-exposure).

Remote VM deploy: `./scripts/deploy-remote.sh <host> <user> --service --key` (default port **30080**). Use full profile on first bring-up; `--quick` only after `python3-venv` is installed on the host.

## 5. Signing in

Set `DASHBOARD_PASSWORD` (and optionally `DASHBOARD_USER`, default `admin`) to put the dashboard, its API, and all artifacts behind the Zyvor login screen — `/health` and the HMAC-verified `/webhook/github` stay open. Without a password, the dashboard is open (local-dev mode).

`deploy-remote.sh` handles this automatically: it sets default credentials once per host, persists them (`.zyvor-argus-auth` next to the port file), injects them into the remote `.env` / K8s secret, and prints the credentials in the deploy summary. Pass `--no-auth` to skip.

Sessions are signed cookies (12 h, or 30 days with "remember me"); sign out from the header.

Login and dashboard share the same **dark theme** design system (light mode available via the header toggle).

## 6. Actions — run anything, watch it live

Action cards live in category panels (**Pipeline**, **Visual**, **Quality**, etc.). Click any card to start a job; one runs at a time. A **live panel** appears immediately with:

- macOS Terminal chrome, streaming Playwright/probe output with syntax colors, **per-test ✓/✗ chips** and a running pass/fail tally
- an elapsed timer, **Copy** / **Save** log, and a **Stop** button that kills the run mid-flight
- when it finishes: a full result table with error text, a **💡 likely-cause hint** per failure, 🎬 video and 🔍 trace links, and a **Download HTML · PDF · Markdown · CSV** row — Markdown also gets a one-click **⧉ Copy MD** button

Press **⌘K** (Ctrl-K) or click **Search** for the command palette that launches any action or jumps to **Ask Zyra**.

### CLI-equivalent actions

| Card | CLI equivalent |
|------|----------------|
| ▶ Smoke | `argus test exec` |
| ▶ Full pipeline | `argus test run [--source --spec --pr-number --expand-coverage]` |
| ⚙ Generate | `argus test generate [--source --spec --expand-coverage]` |
| 🔎 Discover | `argus test discover` |
| ✨ Create from English | `argus test create "…" [--execute]` — LLM when a key is set, heuristic parser otherwise |
| 👁 Visual regression | `argus vision regression [--update-baselines]` |
| 🎬 Flow test | `argus flow run <url> --describe "…" \| --steps <file> [--video/--no-video --insecure --username --password]` |
| 📼 HAR record / replay | `argus api har-replay <url> --mode record\|replay --har <path> [--routes …]` |
| 📥 Import codegen | `argus test import-codegen <file> [--run --url …]` |
| 🗺 Route sweep | `argus vision route-sweep <url> --routes "/,/pricing" [--mobile --update-baselines --insecure]` |

### Dashboard-only (API / security families)

| Card | Panel | Notes |
|------|-------|-------|
| 🆚 API contract diff | API | Static OpenAPI breaking-change diff — no engagement |
| 🤝 Contract verify | API | HAR consumer expectations vs live provider — engagement |
| 📦 SCA scan | Security testing | Client-side licenses and/or local `pip-audit`/`npm audit` |
| 🗄 DB assert | Security testing | SELECT-only assertions; `ZYVOR_DB_TESTING_ENABLED` |
| 💥 Chaos inject / 🌐 Chaos webhook | Security testing | Fault injection + resilience rubric; consent + opt-in |
| Requirements + Impact | Requirements | Versioned scores, linked tests, shared data models & flows |

### Web-quality & site actions

| Card | What it does |
|------|--------------|
| 🌐 Test any site | Crawl every page of any URL, generate a check per page, run them all (login + self-signed TLS supported) |
| 🔬 Site audit | Per-page **a11y (axe-core), links, SEO, console errors, performance, security headers** as a pass/warn/fail matrix, ending in an **A–F health grade** |
| 🔀 Compare | Visual pixel-diff two URLs (staging vs prod) — side-by-side + diff image + % |
| 🎲 Flaky check | Run a suite N times; rank tests by flake rate |
| 📸 Screenshot | Capture any URL at desktop / tablet / mobile, full-page optional |

### 🎬 Flow test — drive a user journey, recorded end-to-end

The marquee action. Describe a **multi-step journey** — log in → navigate → click through a wizard → fill fields → assert the outcome — and the agent drives it as one continuous Playwright session **recorded as a single journey video**.

Two input styles (auto-detected):

- **Plain English** — `Go to /products, click Pricing, verify the Pro plan is visible`. Parsed by the LLM when a key is set, otherwise a verb-pattern heuristic.
- **One step per line** — explicit and LLM-free:
  ```
  go to /
  click "Products"
  fill email = qa@example.com
  press Enter
  assert "HyperSDK"
  ```
  Verbs: `goto`/`go to`/`open`/`navigate`, `click`, `fill|type|enter <field> = <value>`, `press`, `wait [for] <sel|ms>`, `assert|verify|expect|check`.

Steps stream live (`✓ step 3: click "Products"`) into the job panel with a running pass/fail tally. The result is a **step table** (order · action · pass/fail · per-step screenshot) with the **journey video embedded inline** and the HTML/PDF/Markdown/CSV download row. Login user/pass and self-signed TLS are supported; toggle **record video** off for a faster headless pass. A step only "passes" if no runtime error (`ReferenceError`, `Something went wrong`, `page.on('pageerror')`) fired during it.

### 🗺 Route sweep — screenshot many routes, diff vs baselines

Give a URL and a comma/newline list of routes; the sweep screenshots each at **desktop (1440×900)** and/or **mobile (375×812)**. On the first run it captures baselines; on later runs it pixel-diffs each shot against its baseline and flags routes over the diff threshold. Dynamic content (canvas, charts, clocks, skeletons) is masked and animations disabled so live apps don't flake the diff. **Update baselines** re-captures. Result is a route × viewport matrix with diff % and thumbnails. Baselines persist under `reports/artifacts/route-baselines/` (PVC-backed).

### Network & security probes (🧰 Probes card)

Ten one-shot checks, each rendered as a table with flagged issues:

| Probe | Checks |
|-------|--------|
| 🔗 Redirects | full redirect chain + hop count |
| 📋 Headers | complete HTTP response headers |
| 🍪 Cookies | Secure / HttpOnly / SameSite flags |
| 🤖 Robots/sitemap | presence + line/URL counts |
| 🔓 Exposed paths | probes `/.env`, `/.git/config`, etc. (SPA-fallback aware) |
| 🔌 API check | status + JSON-path assertion + latency |
| 🗺 Sitemap URLs | fetch sitemap.xml and test every URL |
| 🌍 DNS | A / AAAA / PTR records |
| ↔ CORS | allow-origin/credentials, flags insecure combos |
| 📦 Compression | encoding, cache-control, HTTP version |

Plus **⏱ Load test** (fire N requests at C concurrency → p50/p95/p99 latency + req/s) and **🔒 TLS check** (DNS + certificate issuer, expiry, protocol, SANs).

### Schedules — run on a loop

The **Runs & schedules → Schedules** section turns any supported job into a recurring monitor (5 min – 6 h). A background thread re-triggers due schedules (respecting single-flight). Add a smoke run every 15 min, an audit every hour, a TLS check daily — add/remove from the panel or the ⌘K palette.

Local `spec` and any URL parameters are validated; local paths are restricted to files inside the repository.

## 7. Ask Zyra (optional knowledge panel)

Citation-first Q&A over ingested product docs — see [Tutorial 14](14-ask-zyra-knowledge.md). Side rail **Console → Ask Zyra**, or ⌘K → “Ask Zyra”. The knowledge lamp in the header shows ready / degraded / offline.

## 8. Reports, videos & test health

- Every executed job writes an **HTML / PDF / Markdown / CSV bundle** to `reports/jobs/<ts>-<kind>/` (PVC-backed on K8s) and exposes it in the result panel — Markdown needs no external renderer, so it's always produced even with `ENABLE_PDF_REPORT=false`.
- **Runs & schedules → Videos** lists every recorded test video; **⬇ all videos (zip)** downloads them in one shot.
- **Test health** (Runs & schedules) ranks the worst-offender tests (fail count, fail %, flaky badge) from a per-test index every run appends to.
- **QA Runs** shows the pass-rate sparkline, expandable run rows, and **⬇ export** (runs as JSON).
- **Requirements** panel lists versioned requirements + quality scores; **Impact** groups them by shared data models and flows (`GET /api/v2/requirements`, `…/impact-graph`).
## 9. Cluster ops

- **Pods** cards show CPU/memory (metrics-server), restarts, warnings, and a **⟳ restart** button.
- **⚡ events** panel shows recent namespace events.
- Log drawer: per-container tabs, line-count selector, follow mode, download.

## 10. API endpoints

The page is a thin client over JSON endpoints you can script against:

| Endpoint | Returns |
|----------|---------|
| `GET /api/dashboard/overview` | banner status, namespace, workloads, latest run, server version |
| `GET /api/dashboard/pods` · `…/pods/{name}/logs?lines=&container=` | pod health (with usage) · log tail |
| `DELETE /api/dashboard/pods/{name}` | restart (delete) a pod |
| `GET /api/dashboard/events` · `/api/dashboard/tests` | cluster events · per-test health |
| `GET /api/dashboard/runs?limit=` · `/api/dashboard/videos` · `/api/dashboard/videos.zip` | history · videos · zip |
| `POST /api/dashboard/jobs` `{kind, params}` · `GET /jobs/status` · `POST /jobs/cancel` · `POST /jobs/rerun` | run / watch / stop / rerun a job |
| `GET /api/dashboard/jobs/report.{csv,html,pdf}` | download the last job's report |
| `GET/POST/DELETE /api/dashboard/schedules[/{id}]` | list / add / remove recurring schedules |
| `POST /api/login` · `POST /api/logout` | session auth |
| `GET /reports/…`, `GET /screenshots/…` | static artifacts (report bundles, videos, diffs) |

Read endpoints degrade gracefully (`"available": false`) instead of erroring when no cluster is reachable.
