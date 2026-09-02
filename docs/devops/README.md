# DevOps runbooks — Zyvor Argus

Operational docs for platform / DevOps / SRE teams who wire **argus** into product pipelines and keep Mission Control running.

These are not “feature marketing.” They assume you own staging URLs, CI secrets, artifact retention, and on-call when the gate goes red.

| Runbook | When you need it |
|---------|------------------|
| [01 — CI/CD gate](01-ci-cd-gate-runbook.md) | Add a post-deploy QA job to any repo |
| [02 — Secrets & target policy](02-secrets-target-policy.md) | Private staging, SSRF allowlists, LLM keys |
| [03 — Product specs & feature gates](03-feature-specs-product-repos.md) | Product teams own acceptance criteria; you own the runner |
| [04 — Mission Control ops](04-mission-control-ops.md) | Deploy `serve`, auth, schedules, TLS, k3s |
| [05 — Failure triage](05-failure-triage-oncall.md) | Job red — what to pull, who to page |
| [06 — Pipeline patterns](06-pipeline-patterns.md) | PR / staging / nightly matrices, shards, browsers |

**Related:** [Tutorial 15 — External CI/CD](../tutorials/15-external-cicd-integration.md) · [Remote deploy](../remote-deploy.md) · [Configuration](../configuration.md) · [Troubleshooting](../troubleshooting.md) · [Blog: integrate your features](https://zyvor.dev/blog/zyaiqaagent-integrate-your-features)

## Operating model (one paragraph)

DevOps owns the **runner** (Action/container image pin, secrets, target policy, artifact upload, fail-the-job contract). Product/QA owns the **checks** (markdown specs under `docs/specs/`, `.flow` journeys, OpenAPI URL, optional `tests/manual/` in an agent workspace). Staging URL is the contract between them: `ZYVOR_BASE_URL` always points at a reachable environment after deploy.

## Version pin (do this once)

```text
Image / Action:  zyvorai/argus@v0.9.2
Container:       ghcr.io/zyvorai/zyvor-argus:v0.9.2
```

Do **not** use `:latest` in production gates. Bump the pin in a dedicated PR when you intentionally upgrade.
