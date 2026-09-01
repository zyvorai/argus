# Tutorial 18 — Security testing: engagements, recon, red-teaming, and sandboxed exploitation

Go beyond the 10 read-only probes: misconfig/recon scanning, CVE lookups, LLM red-teaming of Ask Zyra, a CI/CD security gate, attack-graph reporting, and — behind extra gates — sandboxed PoC verification, attack chaining, and credentialed host/cloud pentesting.

**Prerequisites:** [Tutorial 1](01-getting-started.md), [Tutorial 10](10-mission-control-dashboard.md). For the sandboxed-exploitation sections (§6–§8) you'll also need a Kubernetes cluster reachable from wherever `argus serve` runs.

---

## 1. Everything here needs a security engagement first

Every job kind in this tutorial is refused (`400`) unless the request cites a live, sufficiently-scoped **security engagement** — an admin-issued attestation that you're actually authorized to test the target. This is separate from (and in addition to) the SSRF-focused target policy that already guards every network-capable job: target policy blocks *unsafe* destinations (private ranges, cloud metadata); engagements answer *is this specific test run actually authorized*.

Create one from Mission Control (**🔏 Security engagements** card) or the API:

```bash
curl -X POST http://localhost:8080/api/v2/engagements \
  -H 'Content-Type: application/json' \
  -d '{
    "target_pattern": "*.example.com",
    "scope_statement": "authorized pentest, staging + prod, 2026-Q3 engagement",
    "tier": "active_recon"
  }'
```

`target_pattern` matches a job's hostname via the same glob style as `ZYVOR_TARGET_ALLOWLIST` (`*.example.com`, or `*` for "any host" in a trusted dev environment). `tier` is `active_recon` for the recon/red-team job kinds below (§2–§4) and `exploit` for the sandboxed-exploitation kinds (§6–§8) — an `active_recon`-tier engagement is rejected for those. Save the returned `id`; every job below needs it as `engagement_id`. Revoke with `DELETE /api/v2/engagements/{id}`; list with `GET /api/v2/engagements`.

Only `admin` (RBAC role) can create/revoke engagements; `viewer`/`operator` can read them. Set `ZYVOR_ENGAGEMENT_ENFORCEMENT=disabled` to turn this whole gate off for local dev — never in production (refused at startup if `ZYVOR_ENV=production`).

## 2. Misconfig scan

Tech/version fingerprinting, a ~150-path wordlist sweep (vs. the `security_paths` probe's static 7), security-header *value* grading (not just presence), and DNS hygiene (SPF/DMARC/CAA):

```bash
argus guard misconfig-scan https://your-app.example.com --engagement-id <id> --fail-on high
```

Or from Mission Control: the **🕵️ Misconfig scan** card. Findings show up in the **🐞 Findings** panel with a `category` like `admin-panel-exposure`, `missing-security-header`, or `dns-misconfiguration`.

## 3. CVE lookup

Read-only: fingerprints tech/versions from the same signals as §2, then checks each against [OSV.dev](https://osv.dev). No PoC is generated or run.

```bash
argus guard cve-lookup https://your-app.example.com --engagement-id <id>
```

Coverage is intentionally limited to products with a known ecosystem mapping (currently just npm-published JS libraries like jQuery) — everything else reports "no known ecosystem mapping" rather than guessing.

## 4. LLM red-team Ask Zyra

An attacker→judge loop against your own Ask Zyra RAG agent — a curated battery across five categories: prompt injection, system-prompt exfiltration, excessive agency, jailbreaks, and PII/secret exfiltration.

```bash
argus redteam llm --target dashboard_ask --engagement-id <id>
```

`--target dashboard_ask` (the default) tests in-process, no separate credentials needed. `--target v1_qa --base-url <url> --api-key <key>` tests an external `/v1/qa` deployment instead. A failed prompt raises a `high` or `critical` finding tagged with its OWASP LLM Top 10 category (`LLM01`, `LLM06`, `LLM07`, `LLM02`).

## 5. CI/CD security gate

`--fail-on <severity>` on any of the commands above (plus `audit`, which gained a CLI command for the first time in this release) exits non-zero if a finding at/above that severity was raised — wire it into your CI the same way as the exit-code contract in [Tutorial 15](15-external-cicd-integration.md).

To actually block a GitHub PR merge on a confirmed critical, run the scan, then:

```bash
argus guard pr-gate myorg/myrepo 42 --fail-on high
```

This reads `reports/summary.json` from the scan you just ran and posts a `REQUEST_CHANGES` (or `APPROVE`) review plus a `argus/security` commit status — set that status as a required check under **Settings → Branches** to actually enforce it.

## 6. Attack-graph reporting

The `audit` job's HTML report now renders a same-origin Mermaid graph grouping findings by category → severity, whenever the run raised any. No setup needed — it's automatic once findings exist. (Vendored locally at `templates/vendor/mermaid.min.js`, not loaded from a CDN, since the dashboard's CSP is `script-src 'self'`.)

## 7. Sandboxed exploitation: exploit_poc and attack_chain

Everything past this point needs a genuine execution sandbox — a locked-down Kubernetes Job (dropped capabilities, non-root, read-only rootfs, no ServiceAccount token, resource limits, a hard timeout), never the job-runner process itself:

```bash
kubectl apply -f kubernetes/sandbox.yaml   # dedicated namespace + RBAC + default-deny egress
export ZYVOR_SANDBOX_NAMESPACE=argus-sandbox
export ZYVOR_EXPLOIT_EXECUTION_ENABLED=true   # second, independent gate — an exploit-tier engagement alone isn't enough
```

Without `ZYVOR_SANDBOX_NAMESPACE` pointing at a reachable cluster, both job kinds below refuse to run rather than falling back to unsandboxed execution.

**`exploit_poc`** generates a non-destructive verification script via LLM for a described finding — constrained to read-only requests, no floods, and a single `VERIFIED: true/false - reason` output line — and runs it in the sandbox:

```bash
argus guard exploit-poc https://your-app.example.com \
  --finding "SQL injection in ?id= reflects unescaped input" \
  --engagement-id <exploit-tier-id>
```

**`attack_chain`** is `exploit_poc` run in a loop: an LLM planner proposes one next step at a time given every step already confirmed, stopping the moment a step fails to verify or the planner has nothing safe left to propose (capped at 5 steps):

```bash
argus guard attack-chain https://your-app.example.com \
  --objective "escalate SQLi to RCE" \
  --engagement-id <exploit-tier-id>
```

A confirmed multi-step chain raises an extra `critical` finding summarizing the whole escalation path, on top of one `high` finding per confirmed step. Generated PoC source is written to `reports/pocs/<run>/poc.py` with its SHA-256 logged to the audit log (`GET /api/v2/audit`) — every PoC that ran is traceable back to who authorized the engagement that permitted it.

## 8. Credentialed pentesting: host_pentest and cloud_pentest

One more gate on top of everything in §7, plus a specially-imaged sandbox — the default `python:3.12-slim` has neither `paramiko` (SSH) nor the `aws`/`gcloud`/`az` CLIs:

```bash
export ZYVOR_CREDENTIALED_PENTEST_ENABLED=true
export ZYVOR_SANDBOX_HOST_IMAGE=your-registry/zyvor-sandbox-host:latest    # python:3.12-slim + paramiko
export ZYVOR_SANDBOX_CLOUD_IMAGE=your-registry/zyvor-sandbox-cloud:latest  # + aws-cli/gcloud/az
```

**Credentials are never accepted as raw values.** Every secret-shaped field in `creds` (`password`, `private_key`, `secret_access_key`, ...) must be a `{"$secret": "env:NAME"}` reference — the actual value comes from an env var already set on the `argus` server process, resolved only at execution time and injected straight into that one ephemeral sandbox Job. It's never logged, never given to the LLM, and never present in the job result.

```bash
export TARGET_SSH_PASSWORD=...   # set on the argus server itself, not passed on the CLI

argus guard host-pentest internal-host.example.com \
  --finding "SSH allows password auth with a weak default credential" \
  --creds '{"username":"admin","password":{"$secret":"env:TARGET_SSH_PASSWORD"}}' \
  --engagement-id <exploit-tier-id>
```

```bash
export AWS_SECRET=...

argus guard cloud-pentest aws-prod-123456789012 \
  --provider aws \
  --finding "S3 bucket policy allows public write" \
  --creds '{"access_key_id":"AKIA...","secret_access_key":{"$secret":"env:AWS_SECRET"}}' \
  --engagement-id <exploit-tier-id>
```

From Mission Control, the **🖥 Host pentest** card builds the same `$secret` reference from a username + auth-method dropdown + a text field for the *env var name* (never the value) — the **☁️ Cloud pentest** card takes the same raw creds JSON the CLI does, so both surfaces share one contract.

## 9. What's still not built

Attack Directory-specific tooling (Kerberos/LDAP enumeration, WinRM) beyond generic SSH, and any lateral-movement/persistence logic, are explicitly out of scope — every job kind in this tutorial is read-only enumeration or non-destructive verification, never real exploitation. See [`ROADMAP.md`](../../ROADMAP.md) for the full design rationale.

## 10. Security notes

- All eight job kinds funnel through one choke-point (`orchestrator/dashboard/jobs.py`'s `_validate()`) regardless of trigger path — dashboard, CLI, `/api/v2/jobs`, or a schedule — so the engagement/opt-in gates can't be bypassed by picking a different entry point.
- `misconfig_scan`/`cve_lookup`/`llm_redteam` need only an `active_recon`-tier engagement. `exploit_poc`/`attack_chain` additionally need `ZYVOR_EXPLOIT_EXECUTION_ENABLED`. `host_pentest`/`cloud_pentest` additionally need `ZYVOR_CREDENTIALED_PENTEST_ENABLED` and a properly-imaged sandbox — three independent gates, all fail-closed by default.
- Per-Job network-egress restriction is attempted in the sandbox (a NetworkPolicy scoped to the target's resolved IPs) but is explicitly best-effort — it has no effect on CNIs that don't enforce NetworkPolicy (notably k3s's default Flannel). The pod security hardening (dropped capabilities, non-root, read-only rootfs) is what actually holds regardless of CNI.

**See also:** [`docs/enterprise-v2.md`](../enterprise-v2.md) for the full environment-variable reference and RBAC role details, [`docs/architecture.md`](../architecture.md) for how these job kinds fit into the pipeline, and [`ROADMAP.md`](../../ROADMAP.md) for design rationale and what's deliberately deferred.
