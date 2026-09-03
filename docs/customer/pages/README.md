# Page-by-page guides

Each guide follows: Purpose → When to use it → How to get there → What you can do → Related pages.

Every route is also listed in the [complete page index](../PAGE_INDEX.md).

## Api

| Page | What it covers |
|------|----------------|
| [API contract diff](api/dashboard-actions-api-contract-diff.md) | Static OpenAPI breaking-change diff between two specs (URL, git:<ref>:<path>, or inline JSON) — no live target, no engagement gate. |
| [API contract](api/dashboard-actions-api-contract.md) | Validate REST endpoints against an OpenAPI schema (Forge preset available). |
| [Auth & session](api/dashboard-actions-auth.md) | Login → reusable session file → logout / expiry / negative auth checks. |
| [Contract verify](api/dashboard-actions-contract-verify.md) | HAR-derived consumer contract verification against a live provider (status, content-type, top-level JSON keys) — requires an active_recon engagement. |
| [Live data](api/dashboard-actions-realtime.md) | Assert WebSocket / SSE streams and optional live-region updates. |

## Console

| Page | What it covers |
|------|----------------|
| [Ask Zyra](console/dashboard-ask.md) | Citation-first product knowledge Q&A — optional Qdrant hybrid RAG. Read-only; does not mutate cluster state. Aligned with Zyra copilot branding across the Zyvor platform. |

## Journeys

| Page | What it covers |
|------|----------------|
| [AI test](journeys/dashboard-actions-ai-test.md) | Describe a goal; the autonomous browser agent drives the app toward it. |
| [Flow test](journeys/dashboard-actions-flow.md) | Multi-step user journey (English or step DSL) with optional login/session, video, and Playwright `trace.zip`. |
| [HAR record / replay](journeys/dashboard-actions-har.md) | Record a HAR while browsing routes, or replay the UI against a captured HAR (offline / deterministic network). |
| [Import codegen](journeys/dashboard-actions-import-codegen.md) | Paste Playwright codegen JS/TS and convert it into Zyvor Argus flow steps (optionally run immediately). |

## Operations

| Page | What it covers |
|------|----------------|
| [Findings](operations/dashboard-findings.md) | Collected issues from API, auth, live-data, vitals, and audit jobs with export/clear. |
| [QA Runs](operations/dashboard-runs.md) | History table of QA runs with pass/fail chips and sparkline trends. |
| [Schedules](operations/dashboard-schedules.md) | Turn smoke, audit, ping, TLS, flow, route sweep, API, realtime, or vitals into a 5 min–6 h loop. |
| [Test health](operations/dashboard-test-health.md) | Worst-offender ranking by fail count, fail %, and flaky badge from the per-test index. |
| [Videos](operations/dashboard-videos.md) | Browse and download recorded journey videos / traces from recent jobs. |

## Overview

| Page | What it covers |
|------|----------------|
| [Command palette](overview/dashboard-command-palette.md) | ⌘K / Ctrl-K or header Search — spotlight to jump to any action, panel, or Ask Zyra. |
| [Hero status](overview/dashboard-hero.md) | Cluster/app health banner with pods, replicas, last QA run, pass rate, next schedule, and knowledge (Ask Zyra) stat tile. |
| [Live job panel](overview/dashboard-job-live.md) | Live panel for the running job — macOS Terminal chrome, syntax-colored streaming log, per-test chips, Stop / download. |
| [Pods](overview/dashboard-pods.md) | Pod cards with phase, restarts, and click-through logs; optional cluster events toggle. |
| [Workloads](overview/dashboard-workloads.md) | Deployment and CronJob strip for the argus namespace (when kube access is available). |
| [Mission Control](overview/dashboard.md) | Live Mission Control console — grouped side rail (Console / Testing / Security / Operations), dark theme, status hero, workloads, pods, category action panels, requirements, schedules, findings, and QA run history. |
| [Login](overview/login.md) | Mission Control sign-in when `DASHBOARD_PASSWORD` is set. Uses the same dark/light design system as the dashboard (charcoal default, blue accent buttons). Argus Enterprise uses Keycloak/OIDC with demo accounts `demo`/`demo` and `ssouser`/`Sso@321` (see the Enterprise SSO chapter in this manual). |

## Pipeline

| Page | What it covers |
|------|----------------|
| [Create from English](pipeline/dashboard-actions-create.md) | Turn an English description into a one-off test (LLM when keyed, heuristic otherwise). |
| [Discover coverage](pipeline/dashboard-actions-discover.md) | Scan repo code/docs for untested routes and pages, then propose coverage. |
| [Generate tests](pipeline/dashboard-actions-generate.md) | Generate Playwright tests from a product spec (local path or GitHub). |
| [Run tests](pipeline/dashboard-actions-run-tests.md) | Run ▶ Smoke (optional grep/shard) or ▶ Full LangGraph pipeline from local or GitHub specs. |

## Probes

| Page | What it covers |
|------|----------------|
| [Load test](probes/dashboard-actions-loadtest.md) | Simple concurrency load test for latency under pressure. |
| [Uptime ping](probes/dashboard-actions-ping.md) | HTTP uptime / latency checks across a list of URLs. |
| [Probes](probes/dashboard-actions-probes.md) | One-shot network & security probes: redirects, headers, cookies, robots, exposed paths, API, sitemap, DNS, CORS, compression. |
| [TLS check](probes/dashboard-actions-tls.md) | Certificate and DNS health for a hostname. |

## Quality

| Page | What it covers |
|------|----------------|
| [Site audit](quality/dashboard-actions-audit.md) | Crawl pages for a11y (axe), broken links, SEO, console, perf, and security headers. |
| [Crawl & test](quality/dashboard-actions-crawl.md) | Crawl an arbitrary site and validate every discovered page. |
| [Flaky check](quality/dashboard-actions-flaky.md) | Re-run the suite N times and surface unstable tests. |
| [Web Vitals](quality/dashboard-actions-vitals.md) | Measure Core Web Vitals (LCP / CLS / INP) with optional device and network throttle. |

## Requirements

| Page | What it covers |
|------|----------------|
| [Requirements impact](requirements/dashboard-requirements-impact.md) | Impact view — requirements grouped by shared data models and business flows extracted during evaluate_quality. |
| [Requirements](requirements/dashboard-requirements.md) | Versioned requirements the pipeline ingested — source, quality score, named issues, linked tests, and version history (read-only). |

## Security

| Page | What it covers |
|------|----------------|
| [Attack chain](security/dashboard-actions-attack-chain.md) | Chains exploit-PoC steps via an LLM planner to confirm a multi-step escalation path — same sandbox and opt-ins as Exploit PoC. |
| [Chaos inject](security/dashboard-actions-chaos-inject.md) | Client-side fault injection (latency / loss / reset / dependency timeout) while a flow or smoke control test observes — needs ZYVOR_CHAOS_INJECTION_ENABLED, exploit engagement, and target consent. |
| [Chaos webhook](security/dashboard-actions-chaos-webhook.md) | Trigger a customer-owned chaos experiment webhook, then run a control test with the same resilience rubric and gates as Chaos inject. |
| [Cloud pentest](security/dashboard-actions-cloud-pentest.md) | Credentialed AWS/GCP/Azure CLI enumeration of a described finding in the sandbox — same opt-ins and credential-reference rules as Host pentest. |
| [CVE lookup](security/dashboard-actions-cve-lookup.md) | Read-only: fingerprints tech/versions and checks them against OSV.dev. No PoC is generated or run — requires a security engagement. |
| [DB assert](security/dashboard-actions-db-assert.md) | Read-only SELECT-only assertion (row_count / cell_equals / column_values) against Postgres, MySQL, or SQLite — needs ZYVOR_DB_TESTING_ENABLED and an engagement; DSN is an env-var reference. |
| [Exploit PoC](security/dashboard-actions-exploit-poc.md) | LLM-generated, non-destructive verification of a described finding, executed in a locked-down Kubernetes sandbox — requires an exploit-tier engagement and an execution opt-in. |
| [Host pentest](security/dashboard-actions-host-pentest.md) | Credentialed SSH enumeration of a described finding via paramiko in the sandbox — needs a third, independent credentialed-pentest opt-in; credentials are always env-var references, never raw values. |
| [LLM red-team](security/dashboard-actions-llm-redteam.md) | Attacker/judge adversarial-prompt battery against Ask Zyra — prompt injection, system-prompt leak, excessive agency, jailbreak, PII/secret leak — requires a security engagement. |
| [Misconfig scan](security/dashboard-actions-misconfig-scan.md) | Tech/version fingerprinting, wordlist-driven path discovery, security-header value grading, and DNS hygiene checks — requires a security engagement. |
| [SCA scan](security/dashboard-actions-sca-scan.md) | Client-side library/license fingerprinting and/or local-checkout pip-audit/npm audit — URL mode needs an engagement; checkout mode is operator-local. |
| [Security engagements](security/dashboard-actions-security-engagements.md) | Create/revoke the admin-issued, target-scoped authorization required before running misconfig scan, CVE lookup, or LLM red-team. |

## Visual

| Page | What it covers |
|------|----------------|
| [Compare URLs](visual/dashboard-actions-compare.md) | Side-by-side visual diff of two URLs (e.g. staging vs production). |
| [Visual regression](visual/dashboard-actions-regression.md) | Pixel-compare visual snapshots against baselines; optionally update baselines. |
| [Route sweep](visual/dashboard-actions-route-sweep.md) | Screenshot many routes (or auto-crawl) and diff against route-sweep baselines. |
| [Screenshot](visual/dashboard-actions-screenshot.md) | Capture desktop / tablet / mobile screenshots of any URL. |

---

52 guides. Regenerate: `node scripts/customer-docs/generate-guide-index.mjs`.
