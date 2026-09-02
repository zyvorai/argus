# 01 — CI/CD gate runbook

**Goal:** After every deploy to staging (or on demand), run argus and **fail the pipeline** if checks fail. Upload reports so humans can debug without SSH.

**Audience:** DevOps adding a job to *any* product repo. No need to vendor the Zyvor Argus source tree for a basic smoke gate.

---

## 0. Preconditions checklist

| Check | Why |
|-------|-----|
| Staging URL is HTTPS (or HTTP allowed explicitly) | Target policy |
| Runner can reach that URL (DNS, SG, VPN, mesh) | Otherwise every run is a false red |
| Linux runner (`ubuntu-latest` or equiv.) | GitHub Action is **Docker-type** — macOS/Windows runners will not work |
| Artifact store available | You will upload `reports/` every time |
| Image pull works | `ghcr.io/zyvorai/zyvor-argus:v0.9.2` (public) |

Smoke test from a jump host before wiring CI:

```bash
curl -fsS -o /dev/null -w '%{http_code}\n' https://staging.example.com/
docker pull ghcr.io/zyvorai/zyvor-argus:v0.9.2
docker run --rm \
  -e ZYVOR_BASE_URL=https://staging.example.com \
  -e ZYVOR_ENV=development \
  -v "$PWD/reports:/app/reports" \
  ghcr.io/zyvorai/zyvor-argus:v0.9.2 \
  test --grep @smoke
echo exit:$?
jq . reports/summary.json
```

If this fails locally, fix networking/policy first — CI will only hide the same error in logs.

---

## 1. GitHub Actions (recommended)

### Minimal gate (post-deploy)

```yaml
# .github/workflows/argus.yml
name: Zyvor QA gate

on:
  workflow_dispatch:
  # Prefer your real deploy signal:
  # deployment_status:
  # workflow_run:
  #   workflows: ["Deploy staging"]
  #   types: [completed]

jobs:
  qa-smoke:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - name: Run argus
        id: qa
        uses: zyvorai/argus@v0.9.2
        with:
          command: test
          target-url: ${{ vars.STAGING_URL }}
          grep: '@smoke'
          fail-on-error: 'true'
          # Private RFC1918 staging — leave development OR set production + allowlist:
          # zyvor-env: production
          # target-allowlist: staging.internal.example.com

      - name: Upload QA artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: argus-${{ github.run_id }}
          path: |
            reports/
            test-results/
            screenshots/
            videos/
            traces/
          if-no-files-found: warn
          retention-days: 14

      - name: Summary for humans
        if: always()
        run: |
          echo "### Zyvor QA" >> "$GITHUB_STEP_SUMMARY"
          echo "- passed: \`${{ steps.qa.outputs.passed }}\`" >> "$GITHUB_STEP_SUMMARY"
          echo "- failed: \`${{ steps.qa.outputs.failed }}\`" >> "$GITHUB_STEP_SUMMARY"
          echo "- exit: \`${{ steps.qa.outputs.exit-code }}\`" >> "$GITHUB_STEP_SUMMARY"
          if [ -f reports/summary.json ]; then
            echo '```json' >> "$GITHUB_STEP_SUMMARY"
            cat reports/summary.json >> "$GITHUB_STEP_SUMMARY"
            echo '```' >> "$GITHUB_STEP_SUMMARY"
          fi
```

### Action inputs you will actually use

| Input | Maps to | Notes |
|-------|---------|--------|
| `command` | CLI verb | `test`, `flow`, `route-sweep`, `vitals`, `api-test`, `run`, … |
| `target-url` | `ZYVOR_BASE_URL` | Required for almost everything |
| `grep` | `ZYVOR_GREP` | e.g. `@smoke` |
| `shard` | `ZYVOR_SHARD` | e.g. `1/4` — use with a matrix |
| `args` | raw CLI tail | e.g. `--steps path` (path must exist *in the image* unless you mount) |
| `zyvor-env` | `ZYVOR_ENV` | `development` (default) vs `production` |
| `target-allowlist` | `ZYVOR_TARGET_ALLOWLIST` | Required for private hosts in production mode |
| `openai-api-key` / `anthropic-api-key` | secrets | Only for LLM commands |
| `fail-on-error` | — | `true` = gate; `false` = report-only |

Outputs: `exit-code`, `passed`, `failed`, `summary-path`.

### Required checks

In GitHub → Settings → Branches → protect `main`: require job `qa-smoke` (or your matrix aggregate) before merge/deploy promotion.

---

## 2. Non-GitHub CI (container contract)

Same image, same exit codes, same `reports/summary.json`.

```bash
docker run --rm \
  -e ZYVOR_BASE_URL="$STAGING_URL" \
  -e ZYVOR_ENV=development \
  -e ZYVOR_GREP='@smoke' \
  -v "$CI_PROJECT_DIR/reports:/app/reports" \
  -v "$CI_PROJECT_DIR/test-results:/app/test-results" \
  ghcr.io/zyvorai/zyvor-argus:v0.9.2 \
  test --grep @smoke
```

**GitLab note:** when you use `image: ghcr.io/...` + `script:`, GitLab overrides ENTRYPOINT — call `argus …` explicitly (see [`templates/ci/gitlab-ci.yml`](../../templates/ci/gitlab-ci.yml)).

Templates: [GitLab](../../templates/ci/gitlab-ci.yml) · [CircleCI](../../templates/ci/circleci-config.yml) · [Jenkins](../../templates/ci/Jenkinsfile) · [Azure](../../templates/ci/azure-pipelines.yml).

---

## 3. Exit-code & summary.json contract (gate logic)

| Command | Exit 0 | Exit 1 | Exit 2 |
|---------|--------|--------|--------|
| `test`, `run`, `flow`, `api-test`, … | all passed | ≥1 failure | (flow) missing `--steps`/`--describe` |
| `route-sweep` | no route over diff threshold | visual change | — |
| `vitals` | all metrics “good” | any below good | — |

`reports/summary.json` (stable schema):

```json
{
  "schema_version": 1,
  "command": "test",
  "target_url": "https://staging.example.com",
  "passed": 18,
  "failed": 0,
  "skipped": 1,
  "total": 19,
  "exit_code": 0,
  "status": "passed"
}
```

Shell gate without trusting process exit alone:

```bash
jq -e '.status == "passed" and .failed == 0' reports/summary.json
```

---

## 4. `.env` gotcha (external repos)

`argus` auto-loads `.env` only next to **its own install**, not your product repo’s `.env`.

In product CI: pass **Action inputs / CI variables / secrets**. Do not expect `cp .env` in the product checkout to configure the Action container.

---

## 5. What this gate does *not* do yet

Built-in `test --grep @smoke` exercises the suite **inside the image** against your URL. That is a reachability + generic smoke gate.

To gate **your product features**, add Path 2–4 from the [feature integration blog](https://zyvor.dev/blog/zyaiqaagent-integrate-your-features) and [runbook 03](03-feature-specs-product-repos.md): specs, flows, OpenAPI, or a maintained agent workspace with `tests/manual/`.

---

## 6. Rollout plan (safe)

1. **Report-only** — `fail-on-error: 'false'` for one week; watch flake rate.  
2. **Warn in Slack** — parse `summary.json` in a soft job.  
3. **Hard gate on staging** — `fail-on-error: 'true'`.  
4. **Promote to prod deploy** only after staging hard gate is green for N days.  
5. Pin image; open upgrade PRs separately.

---

## 7. Ownership

| Item | Owner |
|------|--------|
| Workflow YAML + image pin | DevOps |
| `STAGING_URL` / allowlist vars | DevOps + Platform |
| Flaky `@smoke` failures | QA / product (fix selectors or quarantine) |
| LLM keys | Security / DevOps (vault), never plaintext in YAML |
