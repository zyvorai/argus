# Zyvor Argus — Customer Documentation

**Zyvor Argus** (CLI: `argus`) is the autonomous AI QA agent for Zyvor products — LangGraph specs→Playwright, **Mission Control** (flows, HAR, codegen, API/auth/realtime, vitals, probes), and post-deploy audits. This package is for QA engineers, SREs, and platform operators — not people hacking on the agent source tree.

| You want to… | Open |
|--------------|------|
| **Which product? Community vs Watchfloor** | [Which product](which-product.md) |
| **Install Docker/Helm/Community first** | [Install prerequisites](install-prerequisites.md) |
| Install and first smoke | [Getting Started](getting-started.md) |
| Learn Mission Control | [Using the Dashboard](using-the-dashboard.md) |
| Test zyvor.dev (video + HAR) | [Test zyvor.dev](test-zyvor-dev.md) |
| Ask Zyvor knowledge Q&A | [Tutorial 14](../tutorials/14-ask-zyvor-knowledge.md) |
| Follow a card, step by step | [Page-by-page guides](pages/README.md) |
| Multi-step jobs (flow, HAR, API…) | [Common workflows](workflows.md) |
| Look up any surface | [Complete page index](PAGE_INDEX.md) |
| Deploy, auth, ports, k3s | [Admin basics](admin-basics.md) |
| Enterprise SSO / Keycloak demo logins | [Enterprise SSO / OIDC](enterprise-sso.md) |
| Browse capabilities by theme | [Feature Guide](../zyvor-argus-customer-feature-guide.md) |

## Printable PDFs

```bash
node scripts/customer-docs/build-customer-pdfs.mjs
```

Output lands in [`pdf/`](pdf/):

| PDF | Contents |
|-----|----------|
| `ZyvorArgus-Customer-README.pdf` | This overview |
| `ZyvorArgus-Getting-Started.pdf` | Access, Mission Control basics, workflows |
| `ZyvorArgus-Page-by-Page.pdf` | Complete manual — every dashboard surface |
| `ZyvorArgus-Admin-Basics.pdf` | Deploy, auth, TLS, ports, Enterprise SSO / Keycloak |

The build regenerates indexes first. Check links with `node scripts/customer-docs/check-links.mjs`.

Publish to the product site:

```bash
node scripts/customer-docs/sync-to-website.mjs ../hypersdk-web
```

## Product at a glance

```text
  Mission Control  →  argus serve  (default NodePort / port 30080)
  CLI              →  argus test exec | run | flow | har-replay | …
  Playwright       →  playwright/ + generated & manual suites
  Webhooks         →  POST /webhook/github  (HMAC)
  REST             →  /api/dashboard/*  (session-gated when password set)
```

## How this manual is organized

1. **Getting started** — which product (Community vs Watchfloor), install prerequisites, first smoke.
2. **Using the dashboard** — hero, actions grid, live job panel, ⌘K, schedules.
3. **Page-by-page** — a guide for every Mission Control surface and action card.
4. **Page index** — every surface with a one-line purpose and guide link.
5. **Admin basics** — remote deploy, ports, Mission Control login, k3s vs systemd.
6. **Enterprise SSO** — Keycloak / OIDC, demo logins (`demo`/`demo`, `ssouser`/`Sso@321`), local username/password for Argus Enterprise.

Deep engineering docs live under [`../`](../) (architecture, tutorials, configuration) and are out of scope for this customer package.

## Support surfaces (quick map)

| Need | Typical path |
|------|----------------|
| Status & pods | `/dashboard` hero + Workloads / Pods |
| Smoke / full pipeline | Actions → ▶ Run tests |
| E2E journey + video | Actions → 🎬 Flow test |
| Demo site recording | [Test zyvor.dev](test-zyvor-dev.md) |
| HAR record / replay | Actions → 📼 HAR |
| Import Playwright codegen | Actions → 📥 Import codegen |
| API / auth / live data | Actions → 🔌 / 🔐 / 📡 |
| Continuous monitors | Schedules panel |
| What's broken | Findings panel |
| Enterprise SSO / demo logins | [Enterprise SSO / OIDC](enterprise-sso.md) (`demo`/`demo`) |

---

*ZyvorAI Labs · [zyvor.dev](https://zyvor.dev) · Zyvor Argus (repo `Zyvor Argus`)*
