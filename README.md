# Zyvor Argus

[![Release](https://img.shields.io/github/v/release/zyvorai/argus?label=release&color=2997ff)](https://github.com/zyvorai/argus/releases/latest)
[![CI](https://github.com/zyvorai/argus/actions/workflows/ci.yml/badge.svg)](https://github.com/zyvorai/argus/actions/workflows/ci.yml)
[![Security](https://github.com/zyvorai/argus/actions/workflows/security.yml/badge.svg)](https://github.com/zyvorai/argus/actions/workflows/security.yml)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776ab?logo=python&logoColor=white)](pyproject.toml)
[![Node 20+](https://img.shields.io/badge/node-20%2B-339933?logo=node.js&logoColor=white)](package.json)
[![TypeScript](https://img.shields.io/badge/typescript-Playwright-3178c6?logo=typescript&logoColor=white)](playwright/)

**Autonomous QA for the real world.** Argus reads your requirements, scores them for quality, generates Playwright tests, runs them on every deploy, and shows you exactly what broke — in a live ops console that feels like it belongs on a Mac.

[Why Argus](#why-argus) · [Quick start](#quick-start) · [Mission Control](#mission-control) · [Pipeline](#pipeline-cli) · [Which product?](#which-product) · [Docs](docs/tutorials/README.md) · [zyvor.dev](https://zyvor.dev)

<p align="center">
  <img src="docs/assets/zyvor-dev-mission-control-demo.gif" alt="Mission Control — dark theme, side rail, live terminal job panel" width="720">
</p>

<p align="center">
  <em>Side rail · dark theme · Ask Zyra · macOS Terminal live logs · 20+ QA actions from one console</em>
</p>

---

## Why Argus

| Without Argus | With Argus |
|---------------|------------|
| Specs drift from tests | Requirements are **versioned, scored, and traced** to every generated test |
| “Run smoke” is a tribal ritual | **One command** or one dashboard click — same LangGraph pipeline every time |
| Flaky selectors waste afternoons | **Self-healing autofix** suggests and applies repairs, then re-runs |
| Security checks live in spreadsheets | **Authorized** misconfig/CVE/LLM-red-team jobs with audit trail and sandboxed PoC |
| Five tools for E2E, API, vitals, probes | **Mission Control** — pipeline, journeys, visual, quality, API, probes, security, schedules |

No LLM key required for smoke tests, rule-based parsing, and most dashboard actions. Add a provider when you want richer generation and analysis.

---

## Quick start

Requires Python 3.10+, Node 20+, and Docker (only for the container path). `make install` handles the rest, including Playwright's Chromium download.

```bash
git clone https://github.com/zyvorai/argus.git && cd argus
cp .env.example .env          # set ZYVOR_BASE_URL
make install                    # Python venv + Playwright Chromium
argus test exec --grep @smoke   # first green run — no API key
argus serve --port 8080         # → http://localhost:8080/dashboard
```

**Remote deploy in one command:**

```bash
./scripts/deploy-remote.sh YOUR_HOST YOUR_USER --service --key
# Mission Control on port 30080 — credentials printed in deploy summary
```

Container:

```bash
docker pull ghcr.io/zyvorai/zyvor-argus:v0.9.2
docker run --rm -p 8080:8080 --env-file .env ghcr.io/zyvorai/zyvor-argus:v0.9.2 serve --port 8080 --host 0.0.0.0
```

---

## Mission Control

`argus serve` exposes **Mission Control** at `/dashboard` — the operator console for everything Argus can do.

**Layout**

- **Side rail** — Overview, **Ask Zyra**, Pipeline, Visual, Quality, Journeys, API, Probes, Security, Operations
- **Dark theme default** — charcoal surfaces, blue accent buttons; light mode via header toggle
- **Live job panel** — macOS Terminal chrome, syntax-colored logs, per-test ✓/✗ chips, Stop, HTML/PDF/Markdown/CSV reports
- **⌘K / Search** — command palette to jump to any action
- **Hash routes** — `#pipeline`, `#ask`, `#operations` — bookmarkable panels

**What you can run from the UI**

| Category | Actions |
|----------|---------|
| **Testing** | Smoke & full pipeline · generate & discover tests · English → test · codegen import |
| **Journeys** | **Flow journeys** (one video + trace) · HAR record/replay |
| **Visual & quality** | Visual regression & route sweeps · site audit (a11y/SEO/perf/security grade) · Core Web Vitals · flaky detection |
| **Network** | 10 network probes · load & TLS · API contract & auth/session · WebSocket/SSE |
| **Security** | **Engagements** — misconfig, CVE, LLM red-team, sandboxed PoC (authorized targets only) |
| **Ops** | Recurring **schedules** · **Ask Zyra** (optional citation-first RAG) |

→ [Dashboard tutorial](docs/tutorials/10-mission-control-dashboard.md) · [Customer manual](docs/customer/README.md)

---

## Pipeline (CLI)

```
GitHub / local spec / PDF  →  fetch  →  parse  →  evaluate_quality  →  generate  →  execute
                                      ↓ fail → analyze → autofix → re-run
                                      ↓ pass → report → Slack / Teams / email / GitHub PR comment
```

```bash
argus test run --source github --spec docs/specs/feature.md
argus test run --source document --spec requirements/checkout.pdf
argus flow run https://zyvor.dev --steps docs/assets/zyvor-dev-demo.steps --video
curl localhost:8080/api/v2/requirements   # versioned requirements + quality scores
```

Full command reference: [`docs/test-authoring.md`](docs/test-authoring.md)

---

## Which product?

| You need… | Use |
|-----------|-----|
| **QA agent + Mission Control** (free, Apache-2.0) | **This repo** |
| Hardening inside one `argus serve` (RBAC, durable jobs, SSRF policy) | [Enterprise v2 overlay](docs/enterprise-v2.md) |
| Multi-target **Watchfloor** (SSO, billing, unified findings) | Argus Enterprise — [trial release](https://github.com/zyvorai/argus/releases/tag/v1.1.1-ent-trial) |

---

## Documentation

| Start here | |
|------------|---|
| [Tutorials (1→18)](docs/tutorials/README.md) | Install → dashboard → flows → security |
| [Customer manual](docs/customer/README.md) | Page-by-page Mission Control + PDFs |
| [Feature guide](docs/zyvor-argus-customer-feature-guide.md) | Complete capability reference |
| [Configuration](docs/configuration.md) | Every env var |
| [Remote deploy](docs/remote-deploy.md) | VM, container, or k3s |
| [Ask Zyra (RAG)](docs/tutorials/14-ask-zyra-knowledge.md) | Optional Qdrant knowledge Q&A |

Official site: [zyvor.dev/docs](https://zyvor.dev/docs)

---

## Project layout

```
orchestrator/     LangGraph pipeline, Mission Control API, persistence
agents/           Parser, generator, autofix, probes, red-team, reporter
templates/        Mission Control + login (Jinja2)
playwright/       Test runner, crawl, visual diff
knowledge/        Ask Zyra RAG (optional [knowledge] extra)
kubernetes/       Deployment, CronJob, RBAC
scripts/          deploy-remote.sh, customer-docs, e2e smoke
```

---

## Contributing & license

- **Issues & PRs:** [github.com/zyvorai/argus](https://github.com/zyvorai/argus)
- **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md)
- **License:** Apache 2.0 — [LICENSE](LICENSE)
- **Commercial:** [zyvor.dev](https://zyvor.dev) · [sales@zyvor.dev](mailto:sales@zyvor.dev)

---

<p align="center">
  <a href="https://star-history.com/#zyvorai/argus&Date">
    <img src="https://api.star-history.com/svg?repos=zyvorai/argus&type=Date" alt="Star history for zyvorai/argus" width="600">
  </a>
</p>

<p align="center">
  If Argus saves your team a debugging afternoon, a ⭐ on the repo helps others find it.
</p>
