# Admin Basics (Zyvor Argus)

## Ports & URLs

| Port | Surface | Notes |
|------|---------|--------|
| **30080** | Mission Control (lab / k3s NodePort) | Persisted by `deploy-remote.sh` |
| **8080** | Local `argus serve --port 8080` | Dev default |
| **443 / TLS** | `argus serve --tls` | When terminating TLS in-process |
| **8090** | Argus Enterprise (Watchfloor) | Customer package / Helm Service |
| **30180** | Bundled Keycloak NodePort (typical lab) | Only when Enterprise uses NodePort SSO |

```bash
curl -s http://127.0.0.1:8080/health
# remote lab example:
curl -s http://175.110.122.71:30080/health
```

## Auth — Mission Control (community)

- When `DASHBOARD_PASSWORD` is set, `/dashboard` and `/api/dashboard/*` require a session from `/login`.
- Lab defaults are often **`admin` / `Admin@321`** — rotate for anything exposed.
- Override with `DASHBOARD_USER` / `DASHBOARD_PASSWORD` or host file `.argus-auth`.
- `GET /health` stays open for probes.

## Auth — Argus Enterprise (SSO / OIDC)

Argus Enterprise (Watchfloor) does **not** use `DASHBOARD_PASSWORD`. It uses
OIDC (bundled Keycloak or your IdP) and optionally local username/password.

**Demo accounts** after a default Keycloak install (`keycloak.createTestUsers=true`):

| Username | Password | Notes |
|----------|----------|-------|
| `demo` | `demo` | Quick manual login |
| `ssouser` | `Sso@321` | Default for `scripts/test-login.sh` |

These are smoke-test only — turn them off for production. Full install
options (Helm, BYO OIDC, local auth, manual Docker, troubleshooting):
**[Enterprise SSO / OIDC](enterprise-sso.md)**.

```bash
scripts/test-login.sh https://argus.example.com demo demo
```

## Key environment

| Variable | Purpose |
|----------|---------|
| `ZYVOR_BASE_URL` | Target under test |
| `LLM_PROVIDER` / keys | OpenAI, Anthropic, Azure, Google, Ollama |
| `ZYVOR_PRODUCT_REPO` | GitHub `owner/repo` for specs / issues |
| `ENABLE_MULTI_BROWSER` | Firefox + WebKit projects |
| `ENABLE_AUTH_SETUP` | Playwright setup → `storageState` |
| `ENABLE_EMULATION_PROJECTS` | Dark / reduced-motion / locale projects |
| `ZYVOR_GREP` / `ZYVOR_SHARD` | Default suite filters |
| `ZYVOR_HAR_PATH` | Default HAR for replay |
| `ENABLE_REGRESSION` / `VISUAL_MAX_DIFF_RATIO` | Visual pipeline threshold |
| `ENABLE_AUTOFIX` / `ENABLE_AUTOFIX_APPLY` | Self-healing suggestions / apply |
| `GITHUB_WEBHOOK_SECRET` | HMAC for `POST /webhook/github` |

Canonical list: repo [`.env.example`](https://github.com/hypersdk/zyvor-argus/blob/main/.env.example) and [`docs/configuration.md`](https://github.com/hypersdk/zyvor-argus/blob/main/docs/configuration.md).

## Deploy sketch

```bash
./scripts/deploy-remote.sh <host> <user> --quick --service   # systemd (needs free port)
./scripts/deploy-remote.sh <host> <user> --k3s               # preferred when :30080 is NodePort
```

If k3s already binds **:30080** as the `argus-webhook` NodePort, prefer `--k3s` — bare systemd cannot steal that port.

Logs: `journalctl -u argus -f` or `kubectl logs deploy/argus-webhook`.

For Argus Enterprise Helm / Keycloak deploy steps, see
[Enterprise SSO / OIDC](enterprise-sso.md).

## Security notes

- Always set `DASHBOARD_PASSWORD` before exposing Mission Control pod logs publicly.
- For Enterprise, disable Keycloak demo users (`demo` / `ssouser`) outside eval labs.
- Treat webhook secrets, OIDC client secrets, and LLM keys as production secrets.
- Support: [GitHub issues](https://github.com/hypersdk/zyvor-argus/issues) · [sales@zyvor.dev](mailto:sales@zyvor.dev) for Enterprise.

## Related

- [Getting Started](getting-started.md)
- [Install prerequisites](install-prerequisites.md)
- [Using the Dashboard](using-the-dashboard.md)
- [Enterprise SSO / OIDC](enterprise-sso.md)
- [Login (Mission Control)](pages/overview/login.md)
