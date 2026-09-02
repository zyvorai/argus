# 06 — Pipeline patterns (PR / staging / nightly)

**Goal:** Right-size cost and signal. Not every push needs WebKit × 4 shards × full suite.

---

## 1. Tier model

| Tier | Trigger | Command | Browsers | Fail ship? |
|------|---------|---------|----------|------------|
| **T0 PR smoke** | pull_request | `test --grep @smoke` | Chromium | Optional (warn) or required for UI PRs |
| **T1 Staging gate** | post-deploy staging | `test --grep @smoke` + critical `flow` | Chromium | **Yes** |
| **T2 Pre-prod** | promote to pre-prod | smoke + `api-test` + `vitals` | Chromium | **Yes** |
| **T3 Nightly** | cron | full suite + `ENABLE_MULTI_BROWSER` + route-sweep | Cr+FF+Wk | Report + ticket on fail |
| **T4 Manual** | workflow_dispatch | `run --spec`, `create`, exploratories | as needed | No |

---

## 2. Sharding matrix (GitHub Actions)

```yaml
qa:
  strategy:
    fail-fast: false
    matrix:
      shard: [1/4, 2/4, 3/4, 4/4]
  runs-on: ubuntu-latest
  steps:
    - uses: zyvorai/argus@v0.9.2
      with:
        command: test
        target-url: ${{ vars.STAGING_URL }}
        grep: '@smoke'
        shard: ${{ matrix.shard }}
```

Aggregate: require all shards green, or use a final job that downloads artifacts and `jq`s each `summary.json`.

Shards split **tests**, not browsers. For browsers:

```yaml
matrix:
  browser: [chromium, firefox, webkit]   # if your command/env supports per-browser
# or set ENABLE_MULTI_BROWSER=true on nightly only
```

---

## 3. Staging gate with flow + smoke

```yaml
jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: zyvorai/argus@v0.9.2
        with:
          command: test
          target-url: ${{ vars.STAGING_URL }}
          grep: '@smoke'

  critical-path:
    runs-on: ubuntu-latest
    needs: [smoke]
    steps:
      - uses: actions/checkout@v4
      - name: Flow
        run: |
          docker run --rm \
            -e ZYVOR_BASE_URL=${{ vars.STAGING_URL }} \
            -e ZYVOR_IGNORE_HTTPS_ERRORS=true \
            -v "$PWD/qa/flows:/flows:ro" \
            -v "$PWD/reports:/app/reports" \
            ghcr.io/zyvorai/zyvor-argus:v0.9.2 \
            flow "${{ vars.STAGING_URL }}" --steps /flows/checkout.flow --video
      - if: always()
        uses: actions/upload-artifact@v4
        with:
          name: flow-${{ github.run_id }}
          path: reports/
```

Order: **smoke → critical flow → api-test**. Fail fast on smoke.

---

## 4. Cost controls

| Lever | Effect |
|-------|--------|
| `@smoke` tag discipline | Keeps T0/T1 under ~5–10 min |
| Shard only when suite > ~5 min | Overhead otherwise |
| LLM only on T4 / generate jobs | Avoid per-PR token burn |
| `fail-fast: false` on nightly | Collect full flake picture |
| Artifact retention 7–14 days | Storage |
| Self-hosted runners near staging | Less timeout flake |

---

## 5. Feature-flag aware gates

If the feature is flagged off on staging:

- Spec/flow must assert the **flag-on** experience, **or**  
- Gate job only runs when `vars.FEATURE_X=true`, **or**  
- Separate staging slot (`staging-feature-x.example.com`) for the squad  

Document the URL in the workflow comment. Silent skip of assertions causes false greens.

---

## 6. Promote-to-prod checklist (DevOps)

- [ ] T1 staging hard gate green on the same artifact you promote  
- [ ] T2 api-test + vitals green (if applicable)  
- [ ] No open P1 quarantine on critical flows  
- [ ] Image pin unchanged mid-incident (don’t upgrade agent during a firefight)  
- [ ] Rollback path: previous app version + known-green QA run link  

---

## 7. Observability hooks

- Emit `summary.json` fields to your metrics pipeline (failed count, duration).  
- Alert if staging smoke fails 2× consecutive schedule ticks (Mission Control).  
- Dashboard: link CI run ↔ deploy ID ↔ QA artifact in the same annotation.
