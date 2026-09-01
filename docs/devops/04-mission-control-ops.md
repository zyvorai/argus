# 04 — Mission Control operations

**Goal:** Run `argus serve` as a durable ops console for a team: auth, port, schedules, TLS, upgrades, backups of schedules/config.

---

## 1. Deploy profiles (`deploy-remote.sh`)

From a clone of Zyvor Argus:

```bash
./scripts/deploy-remote.sh user@qa-host --service --port 30080
./scripts/deploy-remote.sh user@qa-host --quick --service          # redeploy
./scripts/deploy-remote.sh user@qa-host --container --service
./scripts/deploy-remote.sh user@qa-host --k3s
```

| Profile | Use when |
|---------|----------|
| Full (default) | First bare-metal / VM bring-up |
| `--quick` | Code/deps refresh, same host |
| `--container` | You standardize on Docker/Podman |
| `--k3s` | Want NodePort + CronJob + RBAC manifests |

Details: [remote-deploy.md](../remote-deploy.md).

**Pin the target under test on the host:**

```bash
# remote .env (or k8s Secret)
ZYVOR_BASE_URL=https://staging.example.com
DASHBOARD_USER=admin
DASHBOARD_PASSWORD='…'
```

Health:

```bash
curl -fsS http://qa-host:30080/health
```

UI: `http://qa-host:30080/dashboard`

---

## 2. Local / bastion serve

```bash
export ZYVOR_BASE_URL=https://staging.example.com
export DASHBOARD_PASSWORD='…'
argus serve --port 8080
# optional TLS in-process:
argus serve --port 8443 --tls
```

Prefer ingress TLS (nginx / Traefik / cloud LB) in shared environments.

---

## 3. Schedules (continuous assurance)

In Mission Control → **Schedules** (or API):

| Example | Interval | Action |
|---------|----------|--------|
| Staging smoke | 15 min | `test --grep @smoke` |
| TLS probe | daily | TLS check card |
| Route sweep | hourly | visual drift on critical routes |
| Vitals | hourly | Core Web Vitals gate |

Schedules are single-flight (no pile-up). If smoke is still running, the next tick waits.

**Ops rule:** Schedules alert humans (Slack/email — see notifications tutorial); CI gates block deploys. Don’t use only schedules as the ship gate.

---

## 4. What to expose on the network

| Path | Auth | Expose? |
|------|------|---------|
| `/health` | open | Yes (LB) |
| `/dashboard`, `/api/dashboard/*` | password session | VPN / private only recommended |
| `/webhook/github` | HMAC secret | Public OK if secret strong |

Corporate SSO in front of Mission Control (oauth2-proxy) is fine — keep `/health` and webhook paths correct in the bypass list.

---

## 5. Resource sizing (rule of thumb)

| Workload | CPU | RAM | Notes |
|----------|-----|-----|-------|
| `serve` idle + light clicks | 1 vCPU | 2 GB | |
| Concurrent Playwright smoke | 2+ vCPU | 4 GB | Chromium is hungry |
| Multi-browser + shards | 4 vCPU | 8 GB | Prefer CI runners over the dashboard host |
| `ENABLE_MULTI_BROWSER` on MC host | — | Prefer dedicated CI | Don’t melt the shared console VM |

Set `ZYVOR_PW_WORKERS=2` (or lower) on small hosts / in-cluster.

---

## 6. Upgrade procedure

1. Read release notes for the new tag.  
2. Staging host: `--quick` or new image tag.  
3. Run smoke once: `argus test exec --grep @smoke`.  
4. Bump CI pin `zyvorai/argus@vX.Y.Z` in product repos (separate PR).  
5. Keep previous image tag pullable for 7 days for rollback.

Rollback: redeploy previous tag; revert workflow pin.

---

## 7. Backup / restore

Persist on the host (or in secrets manager):

- `.env` / k8s Secret (URL, keys, dashboard password)  
- Schedule definitions (export if you script them via API)  
- Visual baselines under `screenshots/baselines/` if this host owns them  
- Port/auth state files under deploy dir (`.zyvor-argus-port`, `.zyvor-argus-auth`) — see remote-deploy notes  

Artifacts (`reports/`, videos) are disposable; retention is CI’s job.

---

## 8. Kubernetes notes

- `--k3s` profile applies manifests under `kubernetes/`.  
- NodePort default aligns with port **30080**.  
- Nightly CronJob ≠ replace product CI gates.  
- Image tags from deploy script are content-unique to avoid stale containerd caches.

For multi-tenant clusters, dedicate a namespace (`argus`) and NetworkPolicy: egress only to staging CIDRs + GHCR + LLM endpoints you allow.
