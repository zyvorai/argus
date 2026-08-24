# Tutorials

Hands-on, step-by-step guides. Follow them in order the first time; each later tutorial assumes the setup from Tutorial 1.

| # | Tutorial | You will learn | Time |
|---|----------|----------------|------|
| 1 | [Getting started](01-getting-started.md) | Install, run smoke tests, read your first report | ~15 min |
| 2 | [From spec to test](02-spec-to-test.md) | Write a markdown spec and turn it into running Playwright tests | ~20 min |
| 3 | [Natural-language tests](03-natural-language-tests.md) | Generate tests from a plain-English sentence | ~10 min |
| 4 | [GitHub integration](04-github-integration.md) | Fetch specs from a repo, comment on PRs, run the webhook server | ~30 min |
| 5 | [Coverage expansion](05-coverage-expansion.md) | Let the agent find untested routes/pages and generate tests for them | ~25 min |
| 6 | [Visual regression](06-visual-regression.md) | Capture baselines and catch pixel-level changes | ~15 min |
| 7 | [Self-healing autofix](07-self-healing-autofix.md) | Automatic selector repair and re-execution on failure | ~20 min |
| 8 | [Notifications & reports](08-notifications-and-reports.md) | Slack, Teams, email, PDF reports | ~15 min |
| 9 | [CI/CD & Kubernetes](09-cicd-and-kubernetes.md) | GitHub Actions workflows, Docker, K8s deployment | ~30 min |
| 10 | [Mission Control dashboard](10-mission-control-dashboard.md) | The live console: 20+ QA actions, UX cues, audits, probes, schedules, reports | ~20 min |
| 11 | [E2E flow tests & route sweeps](11-flow-tests.md) | Drive a multi-step user journey recorded as one video; sweep many routes visually | ~20 min |
| 12 | [API, Auth, Live-data & Web-quality](12-api-auth-realtime.md) | Test the product beyond the page: OpenAPI contracts, auth/session, WebSocket/SSE, Core Web Vitals, device/cross-browser | ~30 min |
| 13 | [Test zyvor.dev with recording](13-test-zyvor-dev-recording.md) | YouTube Mission Control demo + smoke/flow/HAR against https://zyvor.dev | ~15 min |
| 14 | [Ask Zyvor (knowledge RAG)](14-ask-zyvor-knowledge.md) | Optional citation-first product Q&A with Qdrant hybrid retrieval in Mission Control | ~20 min |
| 15 | [External CI/CD integration](15-external-cicd-integration.md) | Drop argus into *any* project's pipeline: reusable GitHub Action, GitLab/CircleCI/Jenkins/Azure templates, exit-code & summary.json contract | ~15 min |
| 16 | [Slack slash-command gateway](16-slack-gateway.md) | Trigger and check on pipeline runs from chat with `/zyvor run <kind>` / `/zyvor status <job_id>` | ~10 min |
| 17 | [Desktop app (macOS)](17-desktop-app.md) | Run Mission Control in a native window instead of a browser tab | ~10 min |
| 18 | [Security testing](18-security-testing.md) | Engagements, misconfig/CVE recon, LLM red-teaming, CI security gate, sandboxed exploit PoC/attack-chain/credentialed pentesting | ~30 min |

**DevOps / SRE:** operational runbooks (gates, secrets, specs, Mission Control, triage, pipeline tiers) → **[docs/devops/](../devops/README.md)**.

Deployment: [**Remote deploy**](../remote-deploy.md) — `deploy-remote.sh` puts the agent + dashboard on any host (bare metal, container, or k3s) in one command.

**Argus Enterprise SSO:** [**Enterprise SSO / OIDC (Keycloak)**](../enterprise-sso-oidc.md) — demo logins (`demo`/`demo`, `ssouser`/`Sso@321`), Helm Keycloak, bring-your-own IdP, or local username/password.

Reference documentation lives alongside these tutorials:

- [Architecture](../architecture.md) — how the pipeline works internally
- [Configuration](../configuration.md) — every environment variable
- [Writing Tests & GitHub Integration](../test-authoring.md) — full command reference
- [Troubleshooting](../troubleshooting.md) — common errors and fixes
- [MCP server (chat-ops)](../mcp-server.md) — trigger and poll QA jobs from any MCP-capable chat agent (e.g. Hermes Agent)
- [DevOps runbooks](../devops/README.md) — CI gates, target policy, on-call triage
- [Enterprise SSO / OIDC](../enterprise-sso-oidc.md) — Keycloak + demo username/password for Argus Enterprise
