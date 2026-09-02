# Tutorial 15 — Integrating argus into any project's CI/CD

Run `argus` as a QA gate inside **your own** repo's pipeline — GitHub Actions, GitLab CI, CircleCI, Jenkins, Azure Pipelines, or anything else that can run a container. This is different from [Tutorial 9](09-cicd-and-kubernetes.md), which documents *this repo's own* workflows and Kubernetes deployment.

**Prerequisites:** none — no checkout of this repo, no `.env` file, no GitHub App. Everything here works against the published container image.

---

## 1. Two integration paths

### (a) GitHub Actions — the reusable Action

```yaml
- uses: zyvorai/argus@v0.9.1
  with:
    command: test
    target-url: https://staging.example.com
    grep: '@smoke'
  # secrets, if a command needs them (ai-test, run, flow --describe, create):
  # with:
  #   openai-api-key: ${{ secrets.OPENAI_API_KEY }}

- name: Publish QA artifacts
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: argus-report
    path: reports/
```

The Action is defined in [`action.yml`](../../action.yml) at the repo root — see its `inputs`/`outputs` for the full list (target-policy knobs, LLM keys, `fail-on-error`). It's a **Docker-type Action**, so it only runs on Linux (`ubuntu-latest`) runners, and it wraps the same `ghcr.io/zyvorai/zyvor-argus` image described below rather than reinstalling Python/Node/Playwright on every run.

Outputs `exit-code`, `passed`, `failed`, `summary-path` are populated from `reports/summary.json` (§4) and can be read in a later step via `${{ steps.<id>.outputs.passed }}`.

### (b) Any other CI — the container image directly

```bash
docker run --rm \
  -e ZYVOR_BASE_URL=https://staging.example.com \
  -v "$PWD/reports:/app/reports" \
  ghcr.io/zyvorai/zyvor-argus:v0.9.1 \
  test --grep @smoke
```

Ready-to-copy starting points for GitLab CI, CircleCI, Jenkins, and Azure Pipelines live in [`templates/ci/`](../../templates/ci/README.md).

---

## 2. The `.env` gotcha

`argus` auto-loads a `.env` file, but only the one colocated with its **own installed package** — never your repository's `.env`, regardless of your working directory (`orchestrator/cli.py`'s `_load_env()`). In an external repo's CI there is no such file, which is fine: pass every setting below as an environment variable or CI secret/variable, exactly as the examples do. Don't rely on committing a `.env` to your own repo and expecting it to be picked up — it won't be.

---

## 3. Command / exit-code contract

| Command | Exit 0 | Exit 1 | Exit 2 |
|---|---|---|---|
| `run`, `test`, `flow`, `api-test`, `ai-test`, `auth-test`, `har-replay`, `realtime` | all checks passed | one or more failures | — |
| `flow` | | | neither `--describe` nor `--steps` given |
| `route-sweep` | no route exceeded the visual diff threshold | one or more routes changed beyond `VISUAL_MAX_DIFF_RATIO` | — |
| `vitals` | every Core Web Vitals metric graded "good" | one or more metrics graded below "good" | — |

`route-sweep` and `vitals` gate on real results as of this release — a CI system relying purely on process exit code can now trust both.

---

## 4. The `reports/summary.json` contract

Every command above writes `reports/summary.json` after it finishes — a small, stable, Zyvor-specific result file that doesn't depend on Playwright's own reporter schema:

```json
{
  "schema_version": 1,
  "command": "test",
  "target_url": "https://staging.example.com",
  "started_at": "2026-08-06T12:00:00+00:00",
  "duration_s": 42.3,
  "passed": 18,
  "failed": 0,
  "skipped": 1,
  "total": 19,
  "exit_code": 0,
  "status": "passed",
  "artifacts": { "raw_json": "reports/results.json" },
  "extra": {}
}
```

- `status` is `"passed"` or `"failed"` — use it if you'd rather branch on one string than compare counts.
- `extra` carries command-specific detail: `route-sweep` → `fail_count`/`new_baselines`/`routes`; `vitals` → `overall` and per-metric grades.
- `schema_version` will only increase for backwards-compatible additions.

Read it from any shell-based CI with `jq`:

```bash
jq -r '.failed' reports/summary.json
```

---

## 5. Environment variables

**Target:**

| Variable | Purpose |
|---|---|
| `ZYVOR_BASE_URL` | URL under test |
| `ZYVOR_GREP` | Playwright `--grep` filter (equivalent to `--grep`) |
| `ZYVOR_SHARD` | Playwright `--shard i/n` |

**Target/SSRF policy** (`orchestrator/security/target_policy.py`) — matters once you're pointing this at a private staging URL from CI:

| Variable | Default | Purpose |
|---|---|---|
| `ZYVOR_ENV` | `development` | `development` is permissive (private/internal targets and plain HTTP allowed). `production` blocks them unless explicitly allowlisted. |
| `ZYVOR_TARGET_ALLOWLIST` | empty | Comma-separated hostnames allowed even in `production` mode |
| `ZYVOR_ALLOW_PRIVATE_TARGETS` | `true` unless `production` | Allow RFC1918/loopback/link-local targets |
| `ZYVOR_ALLOW_HTTP_TARGETS` | `true` unless `production` | Allow plain `http://` (not just `https://`) |
| `ZYVOR_TARGET_ALLOWED_PORTS` | `80,443` | Ports permitted for the target |
| `ZYVOR_TARGET_ALLOWED_CIDRS` | empty | CIDR ranges permitted in addition to the allowlist |

**Testing against a private/internal staging URL from CI:** leave `ZYVOR_ENV=development` (the default) for a quick start, or, to run with the stricter production-mode checks intentionally, set `ZYVOR_ENV=production` **and** `ZYVOR_TARGET_ALLOWLIST=staging.internal.example.com` — otherwise the run will fail closed with a target-policy rejection rather than silently testing the wrong thing.

**LLM (only needed for `ai-test`, `run`, `create`, `flow --describe`):** `LLM_PROVIDER`, `LLM_MODEL`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `AZURE_OPENAI_API_KEY`/`_ENDPOINT`/`_DEPLOYMENT`, `GOOGLE_API_KEY`, `OLLAMA_BASE_URL`. Pass keys as CI secrets, never literals. See [Configuration](../configuration.md) for the complete variable list (this table only covers what's relevant to external CI integration).

---

## 6. Artifacts

| Path | Contents |
|---|---|
| `reports/summary.json` | This tutorial's stable CI contract (§4) |
| `reports/results.json` | Raw Playwright reporter output |
| `reports/qa-summary.html` / `.pdf` | Human-readable pipeline report |
| `reports/jobs/<job-id>/report.{html,csv,md,pdf}` | Per-command report bundle (`flow`, `route-sweep`, `vitals`, etc.) — `.md` pastes cleanly into a PR comment |
| `test-results/` | Playwright traces/screenshots/videos for failed tests |
| `screenshots/{baselines,current,diffs}` | Visual regression assets |

Upload `reports/` (and `test-results/`, `screenshots/`, `videos/`, `traces/` if present) as your CI's artifact type — see the per-system templates in [`templates/ci/`](../../templates/ci/README.md) for the exact syntax.

---

## 7. Troubleshooting

- **"target rejected by policy"** — `ZYVOR_ENV=production` with an unlisted private/internal target. Either add it to `ZYVOR_TARGET_ALLOWLIST` or drop back to `ZYVOR_ENV=development` for CI runs against non-public infrastructure you already trust.
- **Missing browsers / Playwright errors when not using the container** — install via `npx playwright install --with-deps chromium`, or just use the `ghcr.io/zyvorai/zyvor-argus` image, which already bundles them.
- **`ai-test`/`run`/`create` fail immediately** — these require an LLM provider key; there's no rule-based fallback for them.
- **A `.env` you committed to your repo isn't being read** — see §2; use CI env vars/secrets instead.
