# Getting Started with Zyvor Argus

**Wrong product?** If you need multi-target Watchfloor SSO / RBAC / billing, that is
**Argus Enterprise**, not this Mission Control path — see [Which product](which-product.md).
This page is for **Community** Zyvor Argus (CLI + Mission Control).

**Missing Docker / Node / Helm?** Install companion packages first:
[Install prerequisites](install-prerequisites.md).

## What you need

| Requirement | Notes |
|-------------|--------|
| Python 3.11+ + Node 20+ | `make install` wires CLI, npm, and Playwright Chromium |
| Target under test | Set `ZYVOR_BASE_URL` (e.g. `https://zyvor.dev`) |
| Optional LLM | `LLM_PROVIDER` + API key for NL create / richer generation |
| Optional GitHub | `gh auth login` + `ZYVOR_PRODUCT_REPO` for GitHub specs / PR comments |

Full env table: [Admin basics](admin-basics.md) · repo [`.env.example`](../../.env.example).

## 1. Install

```bash
git clone https://github.com/zyvorai/argus.git
cd Zyvor Argus
cp .env.example .env   # set ZYVOR_BASE_URL at minimum
make install           # argus CLI + Playwright browsers
```

## 2. First smoke (no LLM required)

```bash
argus test exec --grep @smoke
```

## 3. Open Mission Control

```bash
argus serve --port 8080
# → http://localhost:8080/dashboard
```

When `DASHBOARD_PASSWORD` is set, sign in at `/login` (defaults often `admin` / `Admin@321` on lab hosts — override via env).

**Argus Enterprise (Watchfloor)** uses Keycloak / OIDC instead. After a default
install, smoke-test with `demo` / `demo` or `ssouser` / `Sso@321` — full guide:
[Enterprise SSO / OIDC](enterprise-sso.md).

## 4. Orient yourself

1. **Overview hero** — pods, replicas, last QA run, pass rate, knowledge (Ask Zyra).
2. **Side rail** — Pipeline, Visual, Quality, Journeys, API, Probes, Security, Operations, **Ask Zyra**.
3. **Live job panel** — macOS Terminal log, ✓/✗ chips, Stop.
4. **Schedules / Findings / QA Runs** — Operations panel.
5. **⌘K / Search** — jump to any action; **theme toggle** for light mode.

## 5. First workflows

### A. Smoke from the UI

Mission Control → ▶ Smoke (optional `@smoke` grep).

### B. Drive a short journey (record video)

Actions → 🎬 Flow test — paste steps or English, run with video recording.

Against the public demo site:

```bash
ZYVOR_BASE_URL=https://zyvor.dev
argus flow run https://zyvor.dev --steps /tmp/zyvor-home.steps --video
```

Full recipe + **watch the journey video**: [Test zyvor.dev](test-zyvor-dev.md).

### C. Full pipeline from a spec

```bash
argus test run --source local --spec path/to/spec.md
```

## Related

- [Which product](which-product.md) — Community vs Watchfloor vs Enterprise v2 overlay
- [Using the Dashboard](using-the-dashboard.md)
- [Test zyvor.dev](test-zyvor-dev.md)
- [Common workflows](workflows.md)
- [Admin basics](admin-basics.md)
- [Enterprise SSO / OIDC](enterprise-sso.md)
- [Page-by-page guides](pages/README.md)

## Operate from the console (UX)

1. Open this route from the nav or command palette and wait for live API data.
2. Use filters/search when present; drill into a row for detail.
3. For mutating actions: confirm role gates and impact before applying.
4. **Empty / fail:** Check service health, auth, and that required CRDs/backends for this domain are installed.
5. **Success:** Live data loads; created/updated objects appear without error toasts.

