# Zyvor Argus

[![Release](https://img.shields.io/github/v/release/hypersdk/zyvor-argus?label=release&color=4c9dff)](https://github.com/hypersdk/zyvor-argus/releases/latest)
[![CI](https://github.com/hypersdk/zyvor-argus/actions/workflows/ci.yml/badge.svg)](https://github.com/hypersdk/zyvor-argus/actions/workflows/ci.yml)
[![Security and Quality](https://github.com/hypersdk/zyvor-argus/actions/workflows/security.yml/badge.svg)](https://github.com/hypersdk/zyvor-argus/actions/workflows/security.yml)
[![CodeQL](https://github.com/hypersdk/zyvor-argus/actions/workflows/codeql.yml/badge.svg)](https://github.com/hypersdk/zyvor-argus/actions/workflows/codeql.yml)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776ab?logo=python&logoColor=white)](pyproject.toml)
[![Container](https://img.shields.io/badge/ghcr.io-hypersdk%2Fzyvor--argus-2496ed?logo=docker&logoColor=white)](https://github.com/hypersdk/zyvor-argus/pkgs/container/zyvor-argus)

**Reads requirements, scores them for quality, generates Playwright tests, runs them after every deploy, and tells you exactly what broke and why — with authorized security testing and a live ops console built in.**

[zyvor.dev/docs](https://zyvor.dev/docs?utm_source=github&utm_medium=zyvor-argus) · [Blog](https://zyvor.dev/blog?utm_source=github&utm_medium=zyvor-argus)

## Which product am I looking at?

| You want… | Product | Where |
|-----------|---------|--------|
| **QA agent + Mission Control** for one app (free, Apache-2.0) | **Zyvor Argus (this repo)** | Keep reading → [Quick Start](#quick-start) |
| Hardening *inside* one `argus serve` (durable jobs, SSRF policy, service tokens) | **Enterprise v2 overlay** | [`docs/enterprise-v2.md`](docs/enterprise-v2.md) — still this OSS repo |
| Multi-target **Watchfloor** (SSO, RBAC, unified findings, billing) in front of one or more `argus serve` targets | **Argus Enterprise** | Separate commercial product — trial package on [OSS releases `v1.1.1-ent-trial`](https://github.com/hypersdk/zyvor-argus/releases/tag/v1.1.1-ent-trial); SSO/demo logins: [`docs/customer/enterprise-sso.md`](docs/customer/enterprise-sso.md); source: private `argus-enterprise` |

**Most people who clone this repo want Community.** Install below, open Mission Control, run a smoke. Argus Enterprise is *not* a fork of this tree — it is a separate control plane that talks to `argus serve` over `/api/v2`.

[![Zyvor Argus · Mission Control — KT Walkthrough](https://i.ytimg.com/vi/I985Uz8vZHk/maxresdefault.jpg)](https://youtu.be/I985Uz8vZHk)

**Full KT walkthrough (YouTube):** sign-in → the autonomous pipeline with a live Smoke test run → visual regression & quality → journeys (flow/HAR/codegen/AI test) → API/performance/realtime checks → network & security probes → security testing (misconfig scan, CVE lookup, LLM red-team, sandboxed exploit verification) → command palette → schedules & run history → Ask Zyvor — [watch](https://youtu.be/I985Uz8vZHk)

## Table of contents

- [Feature Guide](#feature-guide)
- [Which product am I looking at?](#which-product-am-i-looking-at)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [CLI Commands](#cli-commands)
- [Phase Features](#phase-features)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [CI/CD](#cicd)
- [Roadmap Status](#roadmap-status)
- [Enterprise & support](#enterprise--support)
- [License](#license)

## 📖 Feature Guide

**[Wiki](https://github.com/hypersdk/zyvor-argus/wiki)** — operator cheat sheets (CLI, Mission Control, journeys, CI/CD, deploy).

**[Zyvor Argus — Customer Feature Guide](docs/zyvor-argus-customer-feature-guide.md)** — a complete, customer-facing reference covering **Mission Control**, journeys, probes, and optional **Ask Zyvor** knowledge Q&A. Also available as a print-ready **[PDF](docs/zyvor-argus-customer-feature-guide.pdf)**.

An AI-first autonomous testing, security, and requirements-quality platform. Reads requirements from GitHub issues/PRs *or* from local documents (markdown, text, PDF), scores each one for gaps and ambiguity before a single test is written, generates Playwright tests, executes them after every deployment, detects regressions, and produces actionable reports — coordinated end to end by a LangGraph state machine, with zero required LLM key (rule-based fallbacks throughout).

### 🆕 Requirements, quality-scored and versioned

Every requirement Argus ingests — from a GitHub issue or a PDF spec, it doesn't matter which — gets a persistent, versioned record: a 0–100 quality score with *named reasons* (missing acceptance criteria, unmeasurable language, contradictions — never a bare number), full version history, and a live trace to every test generated from it. Edit a requirement and Argus tells you exactly which existing tests may need a second look — before you find out from a broken build.

```bash
# Ingest from a document instead of GitHub
argus test run --source document --spec docs/specs/checkout-flow.pdf

# Query what Argus knows about a requirement
curl $ZYVOR_BASE_URL/api/v2/requirements/req-checkout-flow/history
```

Runs at any scale: SQLite by default for a single instance, or point `ZYVOR_STATE_DB` at a `postgresql://` URL for multi-replica deployments — same interface, zero code changes. Opt into [OpenTelemetry tracing](#environment-variables) (`ZYVOR_OTEL_ENABLED=true`) for a `pipeline.<node>`/`job.execute` span on every run.

Ships with **Mission Control** — a live web console (`argus serve` → `/dashboard`) that runs 20+ QA capabilities on demand with streamed output and HTML/PDF/Markdown/CSV reports: the full test pipeline, **E2E flow tests** (multi-step journey → one video + Playwright trace, cross-browser/device/throttle), **HAR record / replay**, **Playwright codegen import**, **API contract tests** (OpenAPI schema validation + multi-step workflows), **auth & session** tests (reusable login), **live-data** tests (WebSocket/SSE assertions), **Core Web Vitals**, **route sweeps** (visual diff at desktop/mobile), site audits (a11y/SEO/perf/security with an A–F grade), ten network & security probes, load and TLS checks, flaky detection, screenshots, and recurring monitors. **Security testing** — misconfig/recon scanning, read-only CVE lookups, and LLM red-teaming against Ask Zyvor — is gated behind an authorized security engagement (`POST /api/v2/engagements`); see [`docs/architecture.md`](docs/architecture.md) and `ROADMAP.md` for what's built vs. deliberately deferred. Optionally enable **Ask Zyvor** — a citation-first LangChain knowledge agent (Qdrant hybrid retrieval) for product docs Q&A inside the same console ([Tutorial 14](docs/tutorials/14-ask-zyvor-knowledge.md)). See [`docs/tutorials/10-mission-control-dashboard.md`](docs/tutorials/10-mission-control-dashboard.md), [`11-flow-tests.md`](docs/tutorials/11-flow-tests.md), and [`12-api-auth-realtime.md`](docs/tutorials/12-api-auth-realtime.md).

### Mission Control UX

The console is a full-bleed ops surface (glass sticky topbar/footer, larger type, primary **Smoke** CTA, card motion) with a short **boot splash**, a live **signal-field / constellation** canvas, **⌘K** command palette, **NOC wall mode** (double-click the brand), and light **warp** cues (`` ` `` or type `zyvor`). Reduced-motion preferences are respected.

## Architecture

```
GitHub (issues, PRs, deploy events) or a local document (md/txt/pdf)
        │
        ▼
LangGraph Orchestrator (Python)
        │
   fetch → discover → gap_analyze → parse → evaluate_quality → generate → execute
        │                                         │                │
        │                        (persisted, versioned,      {regression, api_validate,
        │                         quality-scored, traced          log_analyze, v8_coverage}
        │                         to its generated tests)          │
        │                                                          ▼
        │                                                        merge_results
        │                                                          │
        │                                              ┌───────────┴──── pass → learn_skills → report → notify
        │                                              └──── fail → analyze → autofix → apply_autofix → report → notify
        ▼
   Playwright (Node.js) + Rust diff (optional)
```

- **Orchestrator**: LangGraph state machine coordinates all pipeline stages; every node gets an OpenTelemetry span when tracing is enabled
- **AI agents**: LLM-provider agnostic via LangChain (OpenAI, Anthropic, Azure, Google, Ollama)
- **Persistence**: SQLite by default (single instance); a Postgres-backed store (`ZYVOR_STATE_DB=postgresql://...`) for multi-replica deployments, same interface either way
- **Test execution**: Playwright (TypeScript) with screenshot, video, trace capture
- **Cursor**: development assistant only — not a runtime dependency

## Quick Start

### Container (v0.8.0)

```bash
docker pull ghcr.io/hypersdk/zyvor-argus:v0.8.0
# or
docker pull ghcr.io/hypersdk/zyvor-argus:latest

docker run --rm --env-file .env ghcr.io/hypersdk/zyvor-argus:v0.8.0 test --grep @smoke
docker run --rm -p 8080:8080 --env-file .env ghcr.io/hypersdk/zyvor-argus:v0.8.0 serve --port 8080 --host 0.0.0.0
```

Release notes: [v0.8.0](https://github.com/hypersdk/zyvor-argus/releases/tag/v0.8.0) · full pull/run guide: [docs/releases.md](docs/releases.md)

### Prerequisites

- Python 3.10+ (3.11+ recommended)
- Node.js 20+
- Git

### Install

```bash
cp .env.example .env
make install
```

### Run smoke tests (no LLM required)

```bash
argus test exec --grep @smoke
```

Against the public demo site (video + HAR): [Tutorial 13](docs/tutorials/13-test-zyvor-dev-recording.md).

### Run full pipeline from GitHub (your product repo)

```bash
# Ensure .env has ZYVOR_PRODUCT_REPO=ssahani/hypersdk-web
gh auth login

# Generate + run tests from a specific markdown file in the repo
argus test run --source github --spec docs/specs/my-feature.md

# Generate tests only
argus test generate --source github --spec docs/specs/my-feature.md
```

See [**Writing Tests & GitHub Integration**](docs/test-authoring.md) for the full command reference.

## Documentation

**Official product docs & blog:** [zyvor.dev/docs](https://zyvor.dev/docs?utm_source=github&utm_medium=zyvor-argus) · [zyvor.dev/blog](https://zyvor.dev/blog?utm_source=github&utm_medium=zyvor-argus)

**Operator wiki:** [https://github.com/hypersdk/zyvor-argus/wiki](https://github.com/hypersdk/zyvor-argus/wiki)

**Customer manual (page-by-page Mission Control):** [`docs/customer/`](docs/customer/README.md) — regenerate guides / PDFs / website sync with `scripts/customer-docs/` (same pattern as Zeus OS).

**New here? Start with the [step-by-step tutorials](docs/tutorials/README.md)** — 15 hands-on guides from install to external CI/CD integration.

| Guide | Description |
|-------|-------------|
| [**Customer docs**](docs/customer/README.md) | Mission Control page-by-page manual · PDFs · `sync-to-website.mjs` |
| [**Enterprise v2**](docs/enterprise-v2.md) | Fail-closed security, SSRF allowlists, durable SQLite jobs, `/api/v2`, RBAC |
| [**Enterprise SSO / OIDC**](docs/enterprise-sso-oidc.md) | Keycloak (or any OIDC IdP), demo logins (`demo`/`demo`, `ssouser`/`Sso@321`), local username/password — also in the [customer manual](docs/customer/enterprise-sso.md) |
| [**Tutorials**](docs/tutorials/README.md) | Getting started, spec-to-test, NL tests, GitHub, coverage, regression, autofix, notifications, CI/CD, dashboard, E2E flow tests |
| [**External CI/CD integration**](docs/tutorials/15-external-cicd-integration.md) | Drop argus into *any* project's pipeline via the reusable [GitHub Action](action.yml), or GitLab/CircleCI/Jenkins/Azure [templates](templates/ci/README.md) |
| [**MCP server (chat-ops)**](docs/mcp-server.md) | `argus-mcp` — trigger and poll QA jobs from any MCP-capable chat agent (e.g. Hermes Agent) over Telegram/Discord/Slack/CLI |
| [**DevOps runbooks**](docs/devops/README.md) | CI gates, secrets/target policy, product specs, Mission Control ops, on-call triage, pipeline tiers |
| [**Architecture**](docs/architecture.md) | Pipeline internals: LangGraph nodes, state, agents, fallback design |
| [**Configuration**](docs/configuration.md) | Complete environment variable reference with defaults |
| [**Writing Tests & GitHub Integration**](docs/test-authoring.md) | Command reference; manual, spec-driven, and NL test creation |
| [**Mission Control dashboard**](docs/tutorials/10-mission-control-dashboard.md) | The live console: 20+ QA actions, UX cues, audits, probes, schedules, reports |
| [**Desktop app (macOS)**](docs/tutorials/17-desktop-app.md) | Native window around Mission Control — `npm run desktop` |
| [**Test zyvor.dev (recording)**](docs/tutorials/13-test-zyvor-dev-recording.md) | Smoke + flow video + HAR against https://zyvor.dev |
| [**Remote deployment**](docs/remote-deploy.md) | `deploy-remote.sh` — bare host, container, or k3s in one command |
| [**Releases & container image**](docs/releases.md) | GHCR image (`v0.8.0` / `latest`), how to pull it, how to cut a release |
| [**Troubleshooting**](docs/troubleshooting.md) | Common errors and fixes |
| [**Contributing**](CONTRIBUTING.md) | Dev setup, conventions, how to add a pipeline stage |
| [**Roadmap**](ROADMAP.md) | Known gaps and deliberate deferrals: test coverage, tracing, horizontal scale |
| [`kubernetes/README.md`](kubernetes/README.md) | Kubernetes deployment |
| [`rust/README.md`](rust/README.md) | Rust `zyvor-diff` screenshot processor |
| [`prompts/examples/vm-create.md`](prompts/examples/vm-create.md) | Example requirement spec |

## CLI Commands

Full examples: [**docs/test-authoring.md**](docs/test-authoring.md)

| Command | Description |
|---------|-------------|
| `argus test exec` | Run hand-written smoke tests only |
| `argus test run --source local --spec <path>` | Full pipeline from a local markdown spec |
| `argus test run --source github --spec <path>` | Full pipeline from a GitHub markdown file |
| `argus test run --source github` | Full pipeline from all GitHub specs/issues |
| `argus test run --source document --spec <path>` | Full pipeline from a local markdown/text/PDF document |
| `argus test generate --spec <path>` | Generate tests from local spec (no run) |
| `argus test generate --source github --spec <path>` | Generate tests from GitHub `.md` (no run) |
| `argus test discover --source github` | List coverage candidates and gaps (no generation) |
| `argus test run --source github --expand-coverage` | Pipeline + generate tests for uncovered routes/pages |
| `argus test create "description"` | Generate tests from plain English |
| `argus test create "description" --execute` | Generate and run NL tests |
| `argus vision regression` | Visual regression check |
| `argus vision regression --update-baselines` | Capture new screenshot baselines |
| `argus flow run <url> --steps <file>` | Drive a multi-step journey, recorded as one video + trace |
| `argus flow run <url> --describe "…"` | Same, from a plain-English journey |
| `argus api har-replay <url> --mode record\|replay --har <path>` | Capture network as HAR, then drive the UI against it |
| `argus test import-codegen <file>` | Convert Playwright codegen JS/TS into flow steps |
| `argus vision route-sweep <url> --auto` | Screenshot every crawled route (desktop/mobile), diff vs baselines |
| `argus api test <base> --spec <url>` | Validate REST endpoints against their OpenAPI schema; `--workflow` for multi-step API flows |
| `argus api auth-test <base> --api-login <path>` | Log in, save a reusable session, assert logout/expiry/negative-auth |
| `argus flow realtime <url> --ws <path>` | Assert WebSocket/SSE streams are live (+ reconnect, live-view) |
| `argus watch vitals <url>` | Core Web Vitals (LCP/CLS/INP) with device + network throttle |
| `argus serve` | GitHub webhook server + Mission Control dashboard (`/dashboard`) |
| `argus serve --tls` | Serve the dashboard over HTTPS (self-signed) |

## Phase Features

### Phase 2 — Regression, API, Logs

| Feature | Flag | Description |
|---------|------|-------------|
| Screenshot regression | `ENABLE_REGRESSION=true` | Pixel diff against baselines in `screenshots/baselines/` |
| API validation | `ENABLE_API_VALIDATION=true` | Validates HTTP status codes from captured API calls |
| Browser log analysis | always on | Console errors and network failures flagged in report |

```bash
# Capture baselines
make regression-update

# Compare against baselines
make regression
```

### Phase 3 — LLM Analysis & Notifications

| Feature | Flag | Description |
|---------|------|-------------|
| LLM failure analysis | `ENABLE_LLM_ANALYSIS=true` | Root cause + fix suggestions from traces/screenshots |
| LLM report summary | `ENABLE_LLM_REPORT=true` | Plain-English PR comment summary |
| PDF report export | `ENABLE_PDF_REPORT=true` | Generates `reports/qa-summary.pdf` from HTML |
| Slack notifications | `SLACK_WEBHOOK_URL` | Rich block-formatted messages |
| Teams notifications | `TEAMS_WEBHOOK_URL` | Adaptive card messages |
| Email notifications | `SMTP_*` env vars | HTML email with PDF attachment |
| K8s deployment | `kubernetes/` | CronJob, Deployment, Service, Ingress |

```bash
# Deploy to Kubernetes (cluster must be running)
make k8s-validate   # offline manifest check
make k8s-apply      # apply to cluster
```

### Phase 4 — Autofix, NL Tests, Multi-browser, Rust

| Feature | Flag | Description |
|---------|------|-------------|
| Autofix suggestions | `ENABLE_AUTOFIX=true` | LLM-powered selector repair after failures |
| Autofix apply + re-run | `ENABLE_AUTOFIX_APPLY=true` | Patch spec files and re-execute (self-healing) |
| NL test creation | `argus test create` | Generate tests from plain English |
| Multi-browser | `ENABLE_MULTI_BROWSER=true` | Chromium + Firefox + WebKit |
| Rust diff processor | `ENABLE_RUST_PROCESSOR=true` | Fast screenshot diff via `zyvor-diff` binary |
| Coverage expansion | `ENABLE_COVERAGE_EXPANSION=true` | Discover untested routes/pages from repo code/docs |
| Live site crawl | `ENABLE_LIVE_CRAWL=true` | BFS crawl of the deployed site into coverage inventory |
| V8 JS coverage | `ENABLE_V8_COVERAGE=true` | Measure JS coverage of test runs, reported as % |
| Mission Control dashboard | `argus serve` → `/dashboard` | Live K8s pod health, log tails, QA run history + trends |

```bash
# Natural language test
argus test create "Verify homepage shows all 14 products" --execute

# Build Rust diff tool
make rust

# Multi-browser (manual)
ENABLE_MULTI_BROWSER=true npx playwright test
```

## Environment Variables

See [**docs/configuration.md**](docs/configuration.md) for the complete annotated reference, and [`.env.example`](.env.example) for a starting template. Key variables:

| Variable | Description |
|----------|-------------|
| `LLM_PROVIDER` | `openai`, `anthropic`, `azure`, `google`, `ollama` |
| `ENABLE_REGRESSION` | Enable screenshot visual regression |
| `ENABLE_API_VALIDATION` | Enable API response validation |
| `ENABLE_LLM_ANALYSIS` | LLM-powered failure analysis |
| `ENABLE_AUTOFIX` | Selector repair suggestions |
| `ENABLE_MULTI_BROWSER` | Run tests on chromium, firefox, webkit |
| `ENABLE_RUST_PROCESSOR` | Use Rust `zyvor-diff` for screenshot comparison |
| `ZYVOR_STATE_DB` | SQLite file path (default) or a `postgresql://...` URL for multi-replica deployments |
| `ZYVOR_OTEL_ENABLED` | `true` to emit OpenTelemetry spans per pipeline node and per job (`OTEL_EXPORTER_OTLP_ENDPOINT` if set, else console) |

## Project Structure

```
├── orchestrator/
│   ├── nodes/            # One node per pipeline stage (fetch, parse, evaluate_quality, generate, execute, ...)
│   ├── persistence/      # MissionControlStore (SQLite) + PostgresStore, identical interface
│   ├── observability/    # Prometheus metrics + optional OpenTelemetry tracing
│   ├── security/         # RBAC, secrets, target-policy, engagement gating, sandboxing
│   ├── dashboard/        # Mission Control API + durable job/schedule service
│   ├── paths.py          # Frozen-binary-aware repo-root resolution
│   └── cli.py, webhook.py, graph.py
├── agents/
│   ├── common/               # Shared Pydantic models + LLM factory
│   ├── parser/                # Requirement parsing (LLM + rule-based)
│   ├── requirement_quality/   # Requirement gap/ambiguity scoring (LLM + rule-based)
│   ├── generator/              # Playwright test generation + quality gate
│   ├── execution/               # Playwright subprocess bridge + artifacts
│   ├── discover/                 # Coverage discovery from code/docs + live crawl
│   ├── coverage/                  # Gap analysis + V8 coverage aggregation
│   ├── regression/                 # Screenshot diff (Pillow / Rust)
│   ├── api_validation/, logs/       # API response checks, console/network log analysis
│   ├── analyzer/, autofix/           # LLM failure analysis, selector repair + apply
│   ├── nl_create/                     # Natural-language test creation
│   ├── exploit/, probes/, redteam/     # Security testing: PoC generation, network/misconfig probes, LLM red-team
│   └── reporter/                        # HTML/PDF reports + GitHub/Slack/Teams/email
├── knowledge/            # Ask Zyvor: RAG ingestion + hybrid retrieval (Qdrant)
├── integrations/mcp/     # MCP server — trigger/poll jobs from any MCP-capable chat agent
├── github_integration/   # GitHub API client, token resolution
├── playwright/           # Config, fixtures, utils, crawl + PDF scripts
├── prompts/               # LLM system prompts (markdown)
├── templates/              # Jinja2 fallback test + HTML report
├── tests/manual/             # Hand-written smoke + visual regression tests
├── tests/generated/           # Generated tests (disposable)
├── docs/                        # Guides + tutorials
├── rust/                         # zyvor-diff screenshot processor
├── kubernetes/                    # K8s manifests
└── docker/                         # Container image
```

## CI/CD

This repo tests itself the same way it tests any product — every push/PR to `main` runs:

- **Lint + unit tests**: `.github/workflows/ci.yml` — ruff, pytest (`tests/unit`), `node --check` on every push/PR
- **Docs & manifests**: same workflow — Kubernetes manifests validated offline (`scripts/validate_k8s_manifests.py`), customer docs checked for staleness against `routes.json`/`page-purposes.json` (`npm run docs:guides` must produce no diff) and broken relative links (`npm run docs:links`)
- **Security & quality**: `.github/workflows/security.yml` — mypy + pytest with a coverage floor across Python 3.10–3.12, `pip-audit`, `bandit`, `npm audit`, `tsc --noEmit`, a Trivy container scan of `docker/Dockerfile.secure`, and a Gitleaks secret scan; also runs weekly
- **Static analysis**: `.github/workflows/codeql.yml` — GitHub CodeQL for Python and JavaScript/TypeScript, on every push/PR and weekly
- **Dependency updates**: `.github/dependabot.yml` — weekly PRs for pip, npm (root + `desktop/`), cargo (`desktop/src-tauri/`), Docker, and GitHub Actions — each one runs through the same CI above before merge
- **Smoke tests**: `.github/workflows/qa-smoke.yml` — push, PR, nightly
- **Multi-browser**: manual `workflow_dispatch` trigger in same workflow
- **Post-deploy**: `.github/workflows/qa-post-deploy.yml` — `repository_dispatch: staging-deployed`
- **Release**: `.github/workflows/release.yml` — on tag push `v*.*.*`, builds and pushes `ghcr.io/hypersdk/zyvor-argus:v0.8.0` (+ `:latest`), builds + smoke-tests the macOS desktop app, and creates a GitHub Release; see [docs/releases.md](docs/releases.md)

Run the unit suite locally:

```bash
pip install -e ".[dev]"
ruff check .
pytest tests/unit -q
```

## Roadmap Status

| Phase | Status | Features |
|-------|--------|----------|
| **1** | Complete | GitHub integration, Playwright, test gen, CI/CD, HTML + PDF reports |
| **2** | Complete | Screenshot regression, API validation, browser log analysis |
| **3** | Complete | LLM failure analysis, Slack/Teams/email, K8s deployment |
| **4** | Complete | Autofix, NL test creation, multi-browser, Rust processor |
| **5** | Complete | Authorized security testing (misconfig scan, CVE lookup, LLM red-team, sandboxed exploit PoC, attack chaining, host/cloud pentesting), Mission Control dashboard, Ask Zyvor knowledge RAG |
| **6** | Complete | Requirements quality pipeline (multi-source ingestion, gap/ambiguity scoring, versioned traceability), Postgres-backed store for multi-replica deployments, optional OpenTelemetry tracing |

See [`ROADMAP.md`](ROADMAP.md) for exactly what's open — genuinely deferred work, and what's blocked by something other than effort (a missing credential, a tool that can't do it), named plainly either way.

## Enterprise & support

Three different things share the word “enterprise” — pick the row that matches what you need:

| | **Community (this repo)** | **Enterprise v2 overlay** | **Argus Enterprise (Watchfloor)** |
|---|---|---|---|
| **What it is** | Free OSS QA agent + Mission Control | Optional hardening *inside* one `argus serve` | Separate multi-target control plane |
| **Repo / package** | [`hypersdk/zyvor-argus`](https://github.com/hypersdk/zyvor-argus) | Same repo — [`docs/enterprise-v2.md`](docs/enterprise-v2.md) | Private source; [trial release](https://github.com/hypersdk/zyvor-argus/releases/tag/v1.1.1-ent-trial) |
| **UI** | Mission Control (`argus serve` → `/dashboard`) | Same Mission Control | Watchfloor (SSO, target bar, cross-target findings) |
| **Identity** | Optional `DASHBOARD_PASSWORD` / API tokens | Hashed service tokens + RBAC scopes | OIDC / Keycloak (`demo`/`demo`) or local username/password |
| **When to use** | One team, one (or few) targets | Production hardening of a single deploy | Org-wide governance across many targets |
| **Support** | [GitHub Issues](https://github.com/hypersdk/zyvor-argus/issues) | Same | [sales@zyvor.dev](mailto:sales@zyvor.dev) |

**Community get started:** install toolchain if needed ([install-prerequisites.md](docs/customer/install-prerequisites.md)) → [Quick Start](#quick-start) → customer manual [`docs/customer/getting-started.md`](docs/customer/getting-started.md).

**Watchfloor get started:** [install-prerequisites.md](docs/customer/install-prerequisites.md) (Docker/Helm + Community + token) → trial package → claim → sign in (`demo`/`demo`) → register target → smoke. SSO: [`docs/customer/enterprise-sso.md`](docs/customer/enterprise-sso.md).

Looking for a commercial relationship? Visit **[zyvor.dev](https://zyvor.dev)**.

## License

Apache 2.0 — see [LICENSE](LICENSE).
