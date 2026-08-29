# DevOps Runbooks (Zyvor Argus)

If you own **pipelines, secrets, and "why is staging red?"**, this page is your map. The full checklists and copy-paste YAML live in the repo under [`docs/devops/`](https://github.com/zyvorai/zyvor-argus/tree/main/docs/devops) — this page is the summary.

## 01 — CI/CD gate

Fail the pipeline when checks fail, upload artifacts so humans can debug without SSH. Gate on the process exit code and `reports/summary.json`'s `status`/`failed` fields. Roll out safely: report-only → soft Slack alert → hard staging gate → block prod promote.

Full runbook: [01 — CI/CD gate](https://github.com/zyvorai/zyvor-argus/blob/main/docs/devops/01-ci-cd-gate-runbook.md).

## 02 — Secrets & target policy

Point argus at private staging without leaking credentials or turning the agent into an SSRF foot-gun. Smoke/flow/vitals need no LLM key — only `create`/`ai-test`/LLM `run`/rich `flow --describe` do. `ZYVOR_TARGET_ALLOWLIST` gates which hosts can be tested in production mode.

Full runbook: [02 — Secrets & target policy](https://github.com/zyvorai/zyvor-argus/blob/main/docs/devops/02-secrets-target-policy.md).

## 03 — Product specs & feature gates

Product/QA describe features in the **product** repo (`docs/specs/*.md`, `qa/flows/*.flow`, an OpenAPI URL); DevOps wires them into a gate. The agent is the runner, not the source of truth.

Full runbook: [03 — Feature specs](https://github.com/zyvorai/zyvor-argus/blob/main/docs/devops/03-feature-specs-product-repos.md).

## 04 — Mission Control operations

Running `argus serve` as a durable ops console for a team: auth, port, schedules, TLS, upgrades, backups of schedules/config. Schedules are continuous assurance (e.g. smoke every 15 min); CI gates are ship blockers — use both, don't confuse them.

Full runbook: [04 — Mission Control ops](https://github.com/zyvorai/zyvor-argus/blob/main/docs/devops/04-mission-control-ops.md).

## 05 — Failure triage (on-call)

CI or Mission Control went red — decide in under 15 minutes: infra, product bug, flake, or policy. Download artifacts (`summary.json`, HTML, trace, video) first, classify, one controlled re-run, then fix or quarantine with a ticket ID.

Full runbook: [05 — Failure triage](https://github.com/zyvorai/zyvor-argus/blob/main/docs/devops/05-failure-triage-oncall.md).

## 06 — Pipeline patterns

Right-size cost vs. signal across PR / post-deploy / pre-prod / nightly tiers — not every push needs WebKit × 4 shards × the full suite.

Full runbook: [06 — Pipeline patterns](https://github.com/zyvorai/zyvor-argus/blob/main/docs/devops/06-pipeline-patterns.md).

## Related

- [Admin Basics](admin-basics.md)
- [Enterprise SSO / OIDC](enterprise-sso.md)
- [Getting Started](getting-started.md)
- [Using the Dashboard](using-the-dashboard.md)

## Operate from the console (UX)

1. Open this route from the nav or command palette and wait for live API data.
2. Use filters/search when present; drill into a row for detail.
3. For mutating actions: confirm role gates and impact before applying.
4. **Empty / fail:** Check service health, auth, and that required CRDs/backends for this domain are installed.
5. **Success:** Live data loads; created/updated objects appear without error toasts.

