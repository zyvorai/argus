# 02 — Secrets & target policy runbook

**Goal:** Point argus at private staging without leaking credentials, and without the agent becoming an SSRF foot-gun.

---

## 1. Secret inventory

| Secret | Required for | Where to store |
|--------|--------------|----------------|
| (none) | `test`, `flow --steps`, `vitals`, `route-sweep`, most probes | — |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / Azure / Google | `create`, `ai-test`, `run` (LLM path), `flow --describe` with LLM | CI secret store / vault |
| `GITHUB_TOKEN` or App token | `--source github`, PR comments, webhook | Fine-scoped PAT or GitHub App |
| `GITHUB_WEBHOOK_SECRET` | HMAC on `POST /webhook/github` | Same |
| QA user password for flows | `--password` / auth-test | CI secret; rotate; never in specs committed to git |
| `DASHBOARD_PASSWORD` | Mission Control login | Host secret / k8s Secret |
| Bearer JWT for `api-test` | API contract | Short-lived token preferred |
| OIDC client secret / Keycloak admin | Argus Enterprise SSO | Helm stableSecret / vault — see [`docs/customer/enterprise-sso.md`](../customer/enterprise-sso.md) |

**Rules**

- Never commit `.env` with real keys to a product repo for the Action (it will not be read anyway — see runbook 01).  
- Prefer OIDC → short-lived cloud tokens over long-lived PATs when possible.  
- Separate **read** GitHub token (fetch specs) from **write** token (PR comments) if your org requires it.
- Argus Enterprise demo Keycloak users (`demo`/`demo`, `ssouser`/`Sso@321`) are for smoke tests only — disable `keycloak.createTestUsers` outside eval labs ([Enterprise SSO](../customer/enterprise-sso.md)).

---

## 2. Target policy (SSRF / private staging)

Implementation: `orchestrator/security/target_policy.py`.

| Variable | Default | Meaning |
|----------|---------|---------|
| `ZYVOR_ENV` | `development` | `development` = permissive; `production` = strict |
| `ZYVOR_TARGET_ALLOWLIST` | empty | Comma-separated hostnames allowed under production |
| `ZYVOR_ALLOW_PRIVATE_TARGETS` | true unless production | RFC1918 / loopback / link-local |
| `ZYVOR_ALLOW_HTTP_TARGETS` | true unless production | Plain HTTP |
| `ZYVOR_TARGET_ALLOWED_PORTS` | `80,443` | Extra ports must be listed |
| `ZYVOR_TARGET_ALLOWED_CIDRS` | empty | Extra CIDRs |

### Lab / first CI wiring

```bash
ZYVOR_ENV=development
ZYVOR_BASE_URL=https://staging.internal.example.com
```

### Hardened staging gate

```bash
ZYVOR_ENV=production
ZYVOR_BASE_URL=https://staging.internal.example.com
ZYVOR_TARGET_ALLOWLIST=staging.internal.example.com
# optional:
# ZYVOR_ALLOW_PRIVATE_TARGETS=true
# ZYVOR_TARGET_ALLOWED_CIDRS=10.0.0.0/8
```

GitHub Action:

```yaml
with:
  zyvor-env: production
  target-allowlist: staging.internal.example.com
  target-url: https://staging.internal.example.com
```

**Symptom:** `target rejected by policy` → allowlist missing or `ZYVOR_ENV=production` too early. Fix policy; do not disable checks by pointing at a public decoy URL.

---

## 3. Network path from the runner

Draw the path before blaming Playwright:

```text
CI runner → egress SG / proxy → DNS → staging ingress → app
```

Common failures:

| Symptom | Likely cause |
|---------|--------------|
| Timeout / net::ERR_CONNECTION | SG, NetworkPolicy, private DNS from public runner |
| TLS error | Corporate MITM / self-signed — use `--insecure` / `ZYVOR_IGNORE_HTTPS_ERRORS` only on known lab hosts |
| 407 / proxy auth | Set proxy env in the job; document corp proxy |
| Works on laptop, fails in CI | Laptop on VPN; runner is not |

**Self-hosted runners** on the same VPC as staging are the usual fix for private apps. Document which runner label (`runs-on: [self-hosted, staging-qa]`) owns QA.

---

## 4. LLM keys in CI

```yaml
with:
  command: create   # or run / ai-test / flow with --describe
  llm-provider: anthropic
  anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

- Gate **smoke** without LLM (cheaper, deterministic).  
- Gate **feature generation** on a scheduled or manual workflow with keys.  
- Budget alerts on the LLM project; set `fail-on-error` deliberately.

---

## 5. Mission Control auth

```bash
DASHBOARD_USER=admin
DASHBOARD_PASSWORD='…'   # deploy-remote.sh can generate/persist
```

- `/health` stays open (use for LB probes).  
- `/dashboard` and `/api/dashboard/*` session-gated when password set.  
- Webhook uses `GITHUB_WEBHOOK_SECRET` (HMAC), independent of dashboard login.  
- Rotate lab default `Admin@321` before any internet exposure.

TLS: `argus serve --tls` or terminate at ingress (preferred in prod).

---

## 6. Audit checklist (security review)

- [ ] Image digests or immutable tags pinned  
- [ ] No LLM keys in workflow logs (mask secrets)  
- [ ] Production target policy on shared/prod-like runners  
- [ ] Artifact retention ≤ org policy (reports may contain PII from pages)  
- [ ] QA credentials are non-prod users with minimal roles  
- [ ] Webhook secret set if GitHub → agent automation is enabled  
