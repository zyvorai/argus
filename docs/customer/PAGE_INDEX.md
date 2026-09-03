# Zyvor Argus — Complete page index

Every Mission Control surface and action card.

_52 routes_

Regenerate: `node scripts/customer-docs/generate-page-index.mjs`

## Overview

| Page | Route | Purpose | Guide |
|------|-------|---------|-------|
| Mission Control | `/dashboard` | Live Mission Control console — grouped side rail (Console / Testing / Security / Operations), dark theme, status hero, workloads, pods, category action panels, requirements, schedules, findings, and QA run history. | [Open](pages/overview/dashboard.md) |
| Login | `/login` | Mission Control sign-in — same dark/light design system as the dashboard; DASHBOARD_PASSWORD gate. Argus Enterprise uses Keycloak SSO (demo/demo) — see customer/enterprise-sso.md. | [Open](pages/overview/login.md) |
| Hero status | `/dashboard/hero` | Cluster/app health banner with pods, replicas, last QA run, pass rate, next scheduled smoke, and knowledge (Ask Zyra) status. | [Open](pages/overview/dashboard-hero.md) |
| Workloads | `/dashboard/workloads` | Deployment and CronJob strip for the argus namespace (when kube access is available). | [Open](pages/overview/dashboard-workloads.md) |
| Pods | `/dashboard/pods` | Pod cards with phase, restarts, and click-through logs; optional cluster events toggle. | [Open](pages/overview/dashboard-pods.md) |
| Live job panel | `/dashboard/job-live` | Live panel for the running job — macOS Terminal chrome, syntax-colored log, per-test chips, Copy / Save / Stop. | [Open](pages/overview/dashboard-job-live.md) |
| Command palette | `/dashboard/command-palette` | ⌘K / Ctrl-K or header Search — spotlight to jump to any action, panel, or Ask Zyra. | [Open](pages/overview/dashboard-command-palette.md) |

## Console

| Page | Route | Purpose | Guide |
|------|-------|---------|-------|
| Ask Zyra | `/dashboard/ask` | Ask Zyra — citation-first product knowledge Q&A (optional Qdrant RAG); read-only, no cluster mutations. | [Open](pages/console/dashboard-ask.md) |

## Pipeline

| Page | Route | Purpose | Guide |
|------|-------|---------|-------|
| Run tests | `/dashboard/actions/run-tests` | Run ▶ Smoke (optional grep/shard) or ▶ Full LangGraph pipeline from local or GitHub specs. | [Open](pages/pipeline/dashboard-actions-run-tests.md) |
| Generate tests | `/dashboard/actions/generate` | Generate Playwright tests from a product spec (local path or GitHub). | [Open](pages/pipeline/dashboard-actions-generate.md) |
| Discover coverage | `/dashboard/actions/discover` | Scan repo code/docs for untested routes and pages, then propose coverage. | [Open](pages/pipeline/dashboard-actions-discover.md) |
| Create from English | `/dashboard/actions/create` | Turn an English description into a one-off test (LLM when keyed, heuristic otherwise). | [Open](pages/pipeline/dashboard-actions-create.md) |

## Visual

| Page | Route | Purpose | Guide |
|------|-------|---------|-------|
| Visual regression | `/dashboard/actions/regression` | Pixel-compare visual snapshots against baselines; optionally update baselines. | [Open](pages/visual/dashboard-actions-regression.md) |
| Compare URLs | `/dashboard/actions/compare` | Side-by-side visual diff of two URLs (e.g. staging vs production). | [Open](pages/visual/dashboard-actions-compare.md) |
| Screenshot | `/dashboard/actions/screenshot` | Capture desktop / tablet / mobile screenshots of any URL. | [Open](pages/visual/dashboard-actions-screenshot.md) |
| Route sweep | `/dashboard/actions/route-sweep` | Screenshot many routes (or auto-crawl) and diff against route-sweep baselines. | [Open](pages/visual/dashboard-actions-route-sweep.md) |

## Quality

| Page | Route | Purpose | Guide |
|------|-------|---------|-------|
| Site audit | `/dashboard/actions/audit` | Crawl pages for a11y (axe), broken links, SEO, console, perf, and security headers. | [Open](pages/quality/dashboard-actions-audit.md) |
| Flaky check | `/dashboard/actions/flaky` | Re-run the suite N times and surface unstable tests. | [Open](pages/quality/dashboard-actions-flaky.md) |
| Web Vitals | `/dashboard/actions/vitals` | Measure Core Web Vitals (LCP / CLS / INP) with optional device and network throttle. | [Open](pages/quality/dashboard-actions-vitals.md) |
| Crawl & test | `/dashboard/actions/crawl` | Crawl an arbitrary site and validate every discovered page. | [Open](pages/quality/dashboard-actions-crawl.md) |

## Probes

| Page | Route | Purpose | Guide |
|------|-------|---------|-------|
| Uptime ping | `/dashboard/actions/ping` | HTTP uptime / latency checks across a list of URLs. | [Open](pages/probes/dashboard-actions-ping.md) |
| Load test | `/dashboard/actions/loadtest` | Simple concurrency load test for latency under pressure. | [Open](pages/probes/dashboard-actions-loadtest.md) |
| TLS check | `/dashboard/actions/tls` | Certificate and DNS health for a hostname. | [Open](pages/probes/dashboard-actions-tls.md) |
| Probes | `/dashboard/actions/probes` | One-shot network & security probes: redirects, headers, cookies, robots, exposed paths, API, sitemap, DNS, CORS, compression. | [Open](pages/probes/dashboard-actions-probes.md) |

## Journeys

| Page | Route | Purpose | Guide |
|------|-------|---------|-------|
| Flow test | `/dashboard/actions/flow` | Multi-step user journey (English or step DSL) with optional login/session, video, and trace. | [Open](pages/journeys/dashboard-actions-flow.md) |
| HAR record / replay | `/dashboard/actions/har` | Record a HAR while browsing routes, or replay the UI against a captured HAR. | [Open](pages/journeys/dashboard-actions-har.md) |
| Import codegen | `/dashboard/actions/import-codegen` | Paste Playwright codegen JS/TS and convert it into flow steps (optionally run). | [Open](pages/journeys/dashboard-actions-import-codegen.md) |
| AI test | `/dashboard/actions/ai-test` | Describe a goal; the autonomous browser agent drives the app toward it. | [Open](pages/journeys/dashboard-actions-ai-test.md) |

## API

| Page | Route | Purpose | Guide |
|------|-------|---------|-------|
| API contract | `/dashboard/actions/api-contract` | Validate REST endpoints against an OpenAPI schema (Forge preset available). | [Open](pages/api/dashboard-actions-api-contract.md) |
| API contract diff | `/dashboard/actions/api-contract-diff` | Static OpenAPI breaking-change diff between two specs (URL, git:<ref>:<path>, or inline JSON) — no live target, no engagement gate. | [Open](pages/api/dashboard-actions-api-contract-diff.md) |
| Contract verify | `/dashboard/actions/contract-verify` | HAR-derived consumer contract verification against a live provider (status, content-type, top-level JSON keys) — requires an active_recon engagement. | [Open](pages/api/dashboard-actions-contract-verify.md) |
| Live data | `/dashboard/actions/realtime` | Assert WebSocket / SSE streams and optional live-region updates. | [Open](pages/api/dashboard-actions-realtime.md) |
| Auth & session | `/dashboard/actions/auth` | Login → reusable session file → logout / expiry / negative auth checks. | [Open](pages/api/dashboard-actions-auth.md) |

## Requirements

| Page | Route | Purpose | Guide |
|------|-------|---------|-------|
| Requirements | `/dashboard/requirements` | Versioned requirements the pipeline ingested — source, quality score, named issues, linked tests, and version history (read-only). | [Open](pages/requirements/dashboard-requirements.md) |
| Requirements impact | `/dashboard/requirements/impact` | Impact view — requirements grouped by shared data models and business flows extracted during evaluate_quality. | [Open](pages/requirements/dashboard-requirements-impact.md) |

## Security

| Page | Route | Purpose | Guide |
|------|-------|---------|-------|
| Security engagements | `/dashboard/actions/security-engagements` | Create/revoke the admin-issued, target-scoped authorization required before running any deeper security testing job. | [Open](pages/security/dashboard-actions-security-engagements.md) |
| Misconfig scan | `/dashboard/actions/misconfig-scan` | Tech/version fingerprinting, path discovery, header grading, DNS hygiene, plus compliance signals (security.txt, consent markers, PII patterns) — requires a security engagement. | [Open](pages/security/dashboard-actions-misconfig-scan.md) |
| CVE lookup | `/dashboard/actions/cve-lookup` | Read-only: fingerprints tech/versions and checks them against OSV.dev. No PoC is generated or run — requires a security engagement. | [Open](pages/security/dashboard-actions-cve-lookup.md) |
| SCA scan | `/dashboard/actions/sca-scan` | Client-side library/license fingerprinting and/or local-checkout pip-audit/npm audit — URL mode needs an engagement; checkout mode is operator-local. | [Open](pages/security/dashboard-actions-sca-scan.md) |
| LLM red-team | `/dashboard/actions/llm-redteam` | Attacker/judge adversarial-prompt battery against Ask Zyra — prompt injection, system-prompt leak, excessive agency, jailbreak, PII/secret leak — requires a security engagement. | [Open](pages/security/dashboard-actions-llm-redteam.md) |
| Exploit PoC | `/dashboard/actions/exploit-poc` | LLM-generated, non-destructive verification of a described finding, executed in a locked-down Kubernetes sandbox — requires an exploit-tier engagement and an execution opt-in. | [Open](pages/security/dashboard-actions-exploit-poc.md) |
| Attack chain | `/dashboard/actions/attack-chain` | Chains exploit-PoC steps via an LLM planner to confirm a multi-step escalation path — same sandbox and opt-ins as Exploit PoC. | [Open](pages/security/dashboard-actions-attack-chain.md) |
| Host pentest | `/dashboard/actions/host-pentest` | Credentialed SSH enumeration of a described finding via paramiko in the sandbox — needs a third, independent credentialed-pentest opt-in; credentials are always env-var references, never raw values. | [Open](pages/security/dashboard-actions-host-pentest.md) |
| Cloud pentest | `/dashboard/actions/cloud-pentest` | Credentialed AWS/GCP/Azure CLI enumeration of a described finding in the sandbox — same opt-ins and credential-reference rules as Host pentest. | [Open](pages/security/dashboard-actions-cloud-pentest.md) |
| DB assert | `/dashboard/actions/db-assert` | Read-only SELECT-only assertion (row_count / cell_equals / column_values) against Postgres, MySQL, or SQLite — needs ZYVOR_DB_TESTING_ENABLED and an engagement; DSN is an env-var reference. | [Open](pages/security/dashboard-actions-db-assert.md) |
| Chaos inject | `/dashboard/actions/chaos-inject` | Client-side fault injection (latency / loss / reset / dependency timeout) while a flow or smoke control test observes — needs ZYVOR_CHAOS_INJECTION_ENABLED, exploit engagement, and target consent. | [Open](pages/security/dashboard-actions-chaos-inject.md) |
| Chaos webhook | `/dashboard/actions/chaos-webhook` | Trigger a customer-owned chaos experiment webhook, then run a control test with the same resilience rubric and gates as Chaos inject. | [Open](pages/security/dashboard-actions-chaos-webhook.md) |

## Operations

| Page | Route | Purpose | Guide |
|------|-------|---------|-------|
| Schedules | `/dashboard/schedules` | Turn smoke, audit, ping, TLS, flow, route sweep, API, realtime, or vitals into a 5 min–6 h loop (Runs & schedules panel). | [Open](pages/operations/dashboard-schedules.md) |
| Findings | `/dashboard/findings` | Collected issues from API, auth, live-data, vitals, audit, and security jobs with export/clear. | [Open](pages/operations/dashboard-findings.md) |
| QA Runs | `/dashboard/runs` | History table of QA runs with pass/fail chips and sparkline trends. | [Open](pages/operations/dashboard-runs.md) |
| Videos | `/dashboard/videos` | Browse and download recorded journey videos / traces from recent jobs. | [Open](pages/operations/dashboard-videos.md) |
| Test health | `/dashboard/test-health` | Worst-offender ranking by fail count, fail %, and flaky badge from the per-test index. | [Open](pages/operations/dashboard-test-health.md) |

## Related

- [Customer docs home](README.md)
- [Page-by-page guides](pages/README.md)
