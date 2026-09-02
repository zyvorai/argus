# 03 — Product specs & feature gates

**Goal:** Product/QA describe features; DevOps runs them as a gate. Specs live in the **product** repo; the agent is the **runner**.

---

## 1. Split of ownership

| Artifact | Lives in | Owner |
|----------|----------|--------|
| `docs/specs/*.md` acceptance criteria | Product repo | Product / QA |
| `qa/flows/*.flow` journeys | Product repo | QA |
| OpenAPI URL / file | Product / API repo | API owners |
| Workflow calling argus | Product repo `.github/` | DevOps |
| Image pin `v0.9.2` | Workflow | DevOps |
| Optional long-lived agent checkout with `tests/manual/` | Platform repo or fork | QA + DevOps |

---

## 2. Spec format that CI can trust

```markdown
# Billing upgrade CTA

**As a** customer
**I want to** see upgrade from Billing
**So that** I can change plan

## Acceptance Criteria

1. Page loads at `/billing`
2. Heading `Billing` is visible
3. Click "Upgrade"
4. Content shows `Choose a plan`

## Tags

billing, smoke
```

**Rule-based parser patterns** (no LLM required):

| Criterion text | Step |
|----------------|------|
| `loads at \`/path\`` | navigate |
| `Click "Label"` | click |
| `Enter field: \`value\`` | fill |
| `Heading \`X\` is visible` / `shows \`text\`` | assert |

Put specs under a stable path, e.g. `docs/specs/`. PR template: “New user-facing feature? Add or update a spec.”

---

## 3. Three ways to execute product specs

### A. Developer laptop / agent workspace

```bash
git clone https://github.com/zyvorai/argus.git && cd Zyvor Argus
cp .env.example .env
# .env
ZYVOR_BASE_URL=https://staging.example.com
ZYVOR_PRODUCT_REPO=myorg/my-app
GITHUB_TOKEN=ghp_...   # or gh auth login

make install
argus test run --source github --spec docs/specs/billing-upgrade.md
```

### B. CI with GitHub source (container + env)

```yaml
- name: Feature gate from product specs
  run: |
    docker run --rm \
      -e ZYVOR_BASE_URL=${{ vars.STAGING_URL }} \
      -e ZYVOR_PRODUCT_REPO=${{ github.repository }} \
      -e GITHUB_TOKEN=${{ secrets.GITHUB_TOKEN }} \
      -e ZYVOR_ENV=development \
      -v "$PWD/reports:/app/reports" \
      ghcr.io/zyvorai/zyvor-argus:v0.9.2 \
      run --source github --spec docs/specs/billing-upgrade.md
```

`GITHUB_TOKEN` in Actions already has read access to the same repo’s files in most setups; for private cross-repo specs use a PAT/App.

### C. Flow file in the product repo (no LLM)

Check in `qa/flows/billing.flow`, then either:

- Build a thin wrapper job that `docker run` with a bind-mount of `qa/flows` into the container, **or**
- Checkout Zyvor Argus + copy flows into the workspace before `argus flow run`.

Example mount pattern:

```bash
docker run --rm \
  -e ZYVOR_BASE_URL="$STAGING_URL" \
  -v "$PWD/qa/flows:/flows:ro" \
  -v "$PWD/reports:/app/reports" \
  ghcr.io/zyvorai/zyvor-argus:v0.9.2 \
  flow "$STAGING_URL" --steps /flows/billing.flow --video
```

---

## 4. OpenAPI as the feature contract

```bash
argus api test https://api.staging.example.com \
  --spec https://api.staging.example.com/openapi.json \
  --token "$STAGING_API_TOKEN"
```

CI: run after API deploy, **before** UI smoke if the UI depends on the new contract.

Gate on exit code; upload `reports/`. Schema violations (missing required fields, undeclared 500s) are real findings — fix the API or the OpenAPI, don’t mute the gate.

---

## 5. Promoting generated tests

| Stage | Action |
|-------|--------|
| Spike | `argus test create "…" --execute` (LLM) |
| Review | Spec in `docs/specs/` + `generate` |
| Forever | Move `.spec.ts` → agent `tests/manual/` **or** always `run --spec` from git |

Never treat `tests/generated/` alone as source of truth in CI without regenerating from the spec each run (or promoting to manual).

---

## 6. PR comment loop (optional)

```bash
argus test run --source github \
  --spec docs/specs/billing-upgrade.md \
  --pr-number "$PR_NUMBER"
```

Needs token permission to `pull-requests: write`. Keep comments short; attach artifact links for HTML reports.

---

## 7. Definition of done for a feature (DevOps view)

- [ ] Spec or flow merged in product repo  
- [ ] Staging URL var points at environment that has the feature flag on  
- [ ] Gate job references the new spec/flow  
- [ ] Artifacts retained ≥ 7 days  
- [ ] On-call knows [failure triage](05-failure-triage-oncall.md)  
- [ ] Flake budget: quarantine with `@flaky` / skip only with ticket link  
