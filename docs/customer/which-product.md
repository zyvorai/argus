# Which Argus product do I need?

Short map so Community and Enterprise customers do not mix up three different things.

| You want… | Use | Start here |
|-----------|-----|------------|
| Free QA agent + **Mission Control** for one app | **Zyvor Argus (Community)** — this customer manual’s default path | [Getting Started](getting-started.md) |
| Stronger security *inside* one `argus serve` (durable queue, SSRF allowlist, service tokens) | **Enterprise v2 overlay** (still Community repo) | [Enterprise v2](../enterprise-v2.md) |
| Org **Watchfloor**: SSO, multi-target RBAC, unified findings, billing | **Argus Enterprise** (separate product) | [Enterprise SSO / OIDC](enterprise-sso.md) + trial package on [OSS releases](https://github.com/hypersdk/zyvor-argus/releases) (must include signed `trial.token`) |

## Community path (most readers)

0. Toolchain if needed — [Install prerequisites](install-prerequisites.md) (§1–2)
1. Install / `argus serve` — [Getting Started](getting-started.md)
2. Sign in if `DASHBOARD_PASSWORD` is set (`admin` / lab password) — [Admin basics](admin-basics.md)
3. Run **Smoke** or a **Flow** — [Using the Dashboard](using-the-dashboard.md)

## Watchfloor path (Argus Enterprise)

0. **Install other packages** — Docker/Helm, Community Argus, Bearer token — [Install prerequisites](install-prerequisites.md) (full order)
1. Run **Community** `argus serve` (from step 0).
2. Install Watchfloor (Helm or customer tarball `INSTALL.md` / `PREREQUISITES.md`).
3. Claim owner with the one-time token from logs.
4. Sign in — demo SSO `demo`/`demo` or `ssouser`/`Sso@321`, or local username/password — [Enterprise SSO](enterprise-sso.md).
5. **Add a target** (OSS API URL + app URL + token) → run smoke from Watchfloor.

## Naming trap

“Enterprise v2” in the OSS docs is **not** Watchfloor. Watchfloor is the separate commercial control plane. You can run both: harden each OSS target with the overlay, *and* put Watchfloor in front.

Sales: [sales@zyvor.dev](mailto:sales@zyvor.dev) · [zyvor.dev](https://zyvor.dev)
