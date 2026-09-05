# Unreleased (post-v0.9.2)

Typed impact graph (Order → Payment + canvas), Jira OAuth / IMAP / diarize
sources, Ask Zyra FastEmbed backend, desktop **Remote URL**, and broader
`_job_*` wrapper tests. See `CHANGELOG.md` **[Unreleased]**.

---

# v0.9.2 — Four new test-capability families, requirements impact analysis, cross-replica tracing

Follow-up to **v0.9.1** (docs & version pin refresh to `zyvorai/argus`).

## What's in this release

- **Four new "one-stop" test-capability families** — `api_contract_diff` (pure-Python OpenAPI breaking-change diff), `contract_verify` (HAR-derived consumer contract verification), `sca_scan` (client-side + local-checkout dependency/license scanning), `db_assert` (read-only `SELECT`-only database assertions against Postgres/MySQL/SQLite — Argus's first database access), and `chaos_inject`/`chaos_webhook` (client-side fault injection with a deterministic resilience rubric). Compliance signal checks (`security.txt`, consent-mechanism heuristics, PII-pattern scanning) added to `misconfig_scan`. See `CHANGELOG.md` for full detail, live-verification notes, and what's deliberately deferred.
- **Requirements panel + impact analysis in Mission Control** — a new **Requirements** side-rail panel exposes the requirement-history API that had zero UI since v0.8.0, plus a new "shared data models & flows" impact view (`agents/requirement_entities/`, `GET /api/v2/requirements/impact-graph`).
- **Cross-replica trace propagation** — a job's enqueue and execute spans now link into one OpenTelemetry trace even when they happen on different replicas.
- **`cloud_pentest`'s missing Mission Control card fixed** — it was reachable only via direct API calls before; now has a real UI card, live-verified in a browser.
- **CI coverage gate raised 47 → 50** to match measured 53.47%, keeping the gate meaningful.
- **First real image published under the new registry** — `ghcr.io/zyvorai/zyvor-argus:v0.9.2` is the first tag published since the `hypersdk` → `zyvorai` container registry migration (v0.9.1 only updated docs/pins; no image had been published under the new path yet).
- **Customer PDFs** — regenerated from latest markdown.

## Pull the image

```bash
docker pull ghcr.io/zyvorai/zyvor-argus:v0.9.2
```

## Full changelog

See [CHANGELOG.md](https://github.com/zyvorai/argus/blob/main/CHANGELOG.md).
