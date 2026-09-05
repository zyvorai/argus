# Writing Tests & GitHub Integration

This guide explains how Zyvor Argus creates and runs test cases, and how to connect a GitHub repository as the requirement source.

> New to the project? The [step-by-step tutorials](tutorials/README.md) walk through everything here with worked examples. See also: [Architecture](architecture.md) · [Configuration reference](configuration.md) · [Troubleshooting](troubleshooting.md).

---

## Setup

### 1. Install

```bash
cp .env.example .env
make install
```

### 2. Configure `.env`

Minimum for local testing:

```bash
ZYVOR_BASE_URL=https://zyvor.dev
```

For GitHub spec fetching:

```bash
ZYVOR_PRODUCT_REPO=ssahani/hypersdk-web   # owner/repo — not a full URL
```

For AI-generated tests (optional but recommended):

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

### 3. Authenticate with GitHub

The agent does **not** use Cursor's GitHub login. Use one of:

| Option | Command |
|--------|---------|
| **GitHub CLI** (recommended) | `gh auth login` |
| **Personal access token** | Set `GITHUB_TOKEN=ghp_...` in `.env` |

Credential resolution order: `GITHUB_TOKEN` env var → `gh auth token`.

Refresh an expired CLI token:

```bash
gh auth refresh -h github.com
```

---

## Command reference

### Run tests only (no generation)

```bash
# Run hand-written smoke tests in tests/manual/
argus test exec
```

---

### Write tests from a local markdown spec

```bash
# Generate Playwright tests only (no run)
argus test generate --spec prompts/examples/vm-create.md

# Generate from your own spec file
argus test generate --spec path/to/your-spec.md

# Full pipeline: parse → generate → execute → HTML + PDF report
argus test run --source local --spec prompts/examples/vm-create.md

# Full pipeline with default example spec
argus test run --source local
```

---

### Write tests from a GitHub markdown file

Requires `ZYVOR_PRODUCT_REPO` in `.env` and `gh auth login` (or `GITHUB_TOKEN`).

```bash
# Generate tests from a specific .md file in the product repo
argus test generate --source github --spec docs/specs/my-feature.md

# Full pipeline from a GitHub markdown file
argus test run --source github --spec docs/specs/my-feature.md

# GitHub blob URL also works
argus test run --source github \
  --spec https://github.com/ssahani/hypersdk-web/blob/main/docs/specs/my-feature.md

# Fetch ALL default content (issues + docs/specs/ + README) — no --spec
argus test run --source github

# Post report summary as a PR comment
argus test run --source github --spec docs/specs/my-feature.md --pr-number 42
```

**`--spec` formats accepted with `--source github`:**

| Format | Example |
|--------|---------|
| Repo-relative path | `docs/specs/my-feature.md` |
| GitHub blob URL | `https://github.com/ssahani/hypersdk-web/blob/main/docs/specs/my-feature.md` |
| Raw GitHub URL | `https://raw.githubusercontent.com/ssahani/hypersdk-web/main/docs/specs/my-feature.md` |

When `--spec` is omitted with `--source github`, the agent fetches all default sources (see [What gets fetched from GitHub](#what-gets-fetched-from-github)).

---

### Other requirement sources

| `--source` | Spec / env | Notes |
|------------|------------|-------|
| `document` | Local path (`.md`, `.txt`, PDF, …) | Uses `knowledge/documents.py` extraction |
| `email` | `.eml` path, **or** no path + `IMAP_USER`/`IMAP_PASSWORD` (Gmail app password) | Subject + plain body → markdown |
| `transcript` | `.vtt` / `.srt` / `.txt` / `.md` | Meeting notes without live diarization |
| `jira` | Issue key, JSON export path, and/or `jira_issue_keys` | Prefers `JIRA_OAUTH_ACCESS_TOKEN`; optional refresh via `JIRA_OAUTH_REFRESH_*`; else Basic/Bearer API token |
| `diarize` | Audio (`.wav`/`.mp3`/…) or speaker-tagged `.vtt` | Live audio needs `ZYVOR_DIARIZE_CMD` or `ZYVOR_DIARIZE_API_URL` |

```bash
argus test run --source email --spec inbox/req.eml
argus test run --source jira --spec PROJ-42
argus test run --source diarize --spec meetings/standup.vtt
```

After `evaluate_quality`, Mission Control **Requirements → Impact** shows shared models/flows, co-occurrence edges, and typed dependencies (`Order → Payment`).

---

### Write tests from plain English

```bash
# Generate only
argus test create "Verify homepage loads and shows product suite"

# Generate and run immediately
argus test create "Check /vm page shows migration content" --execute
```

---

### Visual regression

```bash
# Compare screenshots against baselines
argus vision regression

# Capture new baselines
argus vision regression --update-baselines

# Makefile shortcuts
make regression
make regression-update
```

---

### Webhook server (automatic GitHub triggers)

```bash
argus serve --port 8080
```

Configure a webhook on your product repo pointing to `https://<host>:8080/webhook/github` for `push`, `pull_request`, and `repository_dispatch` events.

---

### npm helpers

```bash
npm test                  # Run all Playwright tests
npm run test:manual       # Manual tests only
npm run test:generated    # Generated tests only
npm run report            # Open Playwright HTML report
npm run report:pdf        # Regenerate PDF from reports/qa-summary.html
```

---

## Quick reference table

| Goal | Command |
|------|---------|
| Run smoke tests only | `argus test exec` |
| Generate from local spec | `argus test generate --spec path/to/spec.md` |
| Full pipeline (local spec) | `argus test run --source local --spec path/to/spec.md` |
| Generate from GitHub `.md` | `argus test generate --source github --spec docs/specs/foo.md` |
| Full pipeline (GitHub `.md`) | `argus test run --source github --spec docs/specs/foo.md` |
| Full pipeline (all GitHub specs) | `argus test run --source github` |
| Post report to PR | Add `--pr-number 42` to any `run` command |
| Natural language test | `argus test create "your description"` |
| NL test + run | `argus test create "description" --execute` |
| Visual regression | `argus vision regression` |
| Webhook server | `argus serve` |
| Write tests by hand | Add files to `tests/manual/*.spec.ts` |

---

## Overview: three ways to add tests

| Method | Location | When to use |
|--------|----------|-------------|
| **Manual** | `tests/manual/` | Stable smoke/regression checks you write by hand |
| **Spec-driven** | `tests/generated/` | Requirements in markdown → auto-generated Playwright tests |
| **Natural language** | `tests/generated/` | Quick one-off tests from plain English |

All methods run against `ZYVOR_BASE_URL` (default: `https://zyvor.dev`).

```
Spec / GitHub .md / NL description
        │
        ▼
   Parser agent  ──►  requirements JSON
        │
        ▼
  Generator agent ──►  tests/generated/*.spec.ts
        │
        ▼
   Playwright execute  (+ tests/manual/ always included)
        │
        ▼
   HTML + PDF report
```

---

## 1. Manual tests (hand-written Playwright)

Manual tests live in `tests/manual/` and are **always executed** by the pipeline.

```typescript
// tests/manual/homepage.spec.ts
import { test, expect } from '../../playwright/fixtures/base';
import { waitForPageReady } from '../../playwright/utils/helpers';

test.describe('Zyvor Homepage', () => {
  test('homepage loads with hero content visible', async ({ page, consoleLogs }) => {
    await page.goto('/');
    await waitForPageReady(page);
    await expect(page).toHaveTitle(/Zyvor|HyperSDK/i);
  });
});
```

**Conventions:**

- Use fixtures from `playwright/fixtures/base.ts` (console logs, network errors).
- Use helpers from `playwright/utils/helpers.ts` (`waitForPageReady`, etc.).
- Visual regression tests go in `tests/manual/visual-regression.spec.ts` with baselines under `screenshots/baselines/`.

---

## 2. Spec-driven generation

Write a markdown spec → parser extracts requirements → generator writes Playwright TypeScript.

### Spec format

See [`prompts/examples/vm-create.md`](../prompts/examples/vm-create.md):

```markdown
# Administrator creates a VM — marketing site validation

**As a** visitor
**I want to** see VM and infrastructure capabilities on zyvor.dev
**So that** I can evaluate the Zyvor platform

## Acceptance Criteria

1. Homepage loads at `https://zyvor.dev`
2. VM migration and KubeVirt content is visible
3. HyperSDK / Zeus OS product names are listed
4. `/vm` route serves the marketing site (no dashboard login)

## Tags

vm, marketing, smoke
```

The parser uses an LLM when an API key is set (`prompts/parser.md`); otherwise it falls back to rule-based parsing.

The generator writes one `.spec.ts` per requirement into `tests/generated/`:

- **With LLM** — full Playwright TypeScript from `prompts/generator.md`.
- **Without LLM** — Jinja2 template at `templates/test.spec.ts.j2`.

### Output files

| Artifact | Path |
|----------|------|
| Parsed requirements | `tests/fixtures/requirements.json` |
| Fetched GitHub specs | `tests/fixtures/fetched/` |
| Generated tests | `tests/generated/<id>-<title>.spec.ts` |
| HTML report | `reports/qa-summary.html` |
| PDF report | `reports/qa-summary.pdf` |

---

## 3. Natural language test creation

Uses `agents/nl_create/` and `prompts/nl_create.md` — no markdown spec file needed.

```bash
argus test create "Verify homepage loads and shows product suite"
argus test create "Check /vm page shows migration content" --execute
```

---

## GitHub integration

### Environment variables

| Variable | Required | Format | Example |
|----------|----------|--------|---------|
| `ZYVOR_PRODUCT_REPO` | Yes | `owner/repository` | `ssahani/hypersdk-web` |
| `GITHUB_TOKEN` | No* | PAT or fine-grained token | `ghp_...` |
| `ZYVOR_BASE_URL` | Yes | HTTPS URL | `https://zyvor.dev` |

\*Not required if `gh auth login` is configured.

### Example `.env` for hypersdk-web

```bash
ZYVOR_PRODUCT_REPO=ssahani/hypersdk-web
ZYVOR_BASE_URL=https://zyvor.dev
# GITHUB_TOKEN=          # optional — use gh auth login instead
```

### What gets fetched from GitHub

Content is saved to `tests/fixtures/fetched/`:

| When | Source | Content |
|------|--------|---------|
| `--spec` provided | Single file | Only that `.md` file |
| No `--spec` | Open issues labeled `qa`, `user-story`, `feature-spec`, `enhancement` | Issue title + body → `issue-<number>.md` |
| No `--spec` | `docs/specs/` | All `.md` files in that directory |
| No `--spec` | Root | `CHANGELOG.md`, `README.md` |

**Tip:** Put specs in `docs/specs/` in your product repo, or label issues with `qa`.

### Verify GitHub access

```bash
export $(grep -v '^#' .env | xargs)
curl -s -H "Authorization: Bearer $(gh auth token)" \
  https://api.github.com/repos/$ZYVOR_PRODUCT_REPO | grep full_name
```

---

## Coverage expansion from GitHub code and docs

When enabled, the agent reads product repo docs and code signals, compares them against existing Playwright tests, and generates missing coverage tests.

### Enable coverage expansion

```bash
# One-off via CLI flag
argus test run --source github --expand-coverage
argus test generate --source github --expand-coverage

# Or set in .env for webhook/default GitHub runs
ENABLE_COVERAGE_EXPANSION=true
COVERAGE_MAX_NEW_TESTS=10
```

### Discover without generating tests

```bash
argus test discover --source github
argus test discover --source github --pr-number 42
```

### What gets scanned

Default discovery roots (override with `COVERAGE_DISCOVERY_PATHS`):

| Path | Signals extracted |
|------|-------------------|
| `docs/`, `docs/specs/` | Markdown headings → page candidates |
| `README.md`, `CHANGELOG.md` | Document sections |
| `src/pages/`, `src/routes/`, `app/` | Route/page file paths |
| `sidebars*.js/ts`, `docusaurus.config.*` | Sidebar doc IDs |
| `openapi*.json/yaml` | API path candidates |

Downloaded files are saved to `tests/fixtures/fetched/code/`. New tests are written as `tests/generated/coverage-*.spec.ts` (capped by `COVERAGE_MAX_NEW_TESTS`).

### Behavior rules

| Command | Coverage expansion |
|---------|-------------------|
| `--spec docs/foo.md` (no flag) | Spec only — unchanged behavior |
| `--spec docs/foo.md --expand-coverage` | Spec + code/doc discovery |
| No `--spec`, `ENABLE_COVERAGE_EXPANSION=true` | Full discovery on GitHub fetch |
| Webhook `pull_request` / `push` | Scopes discovery to changed files when available |

PR comments include a **Coverage** section with inventory size, gaps remaining, and new tests generated.

### Coverage environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `ENABLE_COVERAGE_EXPANSION` | `false` | Enable discovery on GitHub runs |
| `COVERAGE_MAX_NEW_TESTS` | `10` | Cap new coverage specs per run |
| `COVERAGE_DISCOVERY_PATHS` | see defaults | Comma-separated repo roots |
| `COVERAGE_MAX_DISCOVERY_FILES` | `200` | Max files to download |
| `COVERAGE_MAX_DISCOVERY_BYTES` | `2000000` | Max total bytes to download |

---

## Self-healing (autofix apply + re-execute)

When tests fail, the agent can suggest selector fixes and optionally patch test files and re-run.

```bash
ENABLE_AUTOFIX=true
ENABLE_AUTOFIX_APPLY=true
AUTOFIX_MAX_RETRIES=2
```

Flow: `fail → analyze → autofix → apply_autofix → re-execute` (up to `AUTOFIX_MAX_RETRIES` times).

---

## Live site crawl discovery

Crawl the deployed site to discover routes not found in GitHub docs/code:

```bash
ENABLE_LIVE_CRAWL=true
CRAWL_MAX_PAGES=50
CRAWL_MAX_DEPTH=2
npm run crawl
```

Crawl results merge into the coverage inventory during `discover` when coverage expansion is enabled.

---

## V8 JS code coverage

Collect V8 bytecode coverage during Playwright runs:

```bash
ENABLE_V8_COVERAGE=true
argus test exec
```

Coverage artifacts are written to `reports/v8-coverage/` and summarized in the HTML/PR report.

### Regenerating higher-quality tests

After pipeline updates, delete stale `tests/generated/coverage-*.spec.ts` stubs and regenerate:

```bash
argus test generate --source github --expand-coverage
```

Generated tests now use `playwright/fixtures/base`, `waitForPageReady`, route-specific navigation, and `toBeVisible` assertions. A post-generation quality gate rejects duplicate homepage stubs and wrong-path navigation.

### PR comments and notifications

When `--pr-number` is set, the agent posts a summary on the pull request (including coverage stats when expansion is enabled).

| Channel | Environment variable |
|---------|---------------------|
| Slack | `SLACK_WEBHOOK_URL` |
| Microsoft Teams | `TEAMS_WEBHOOK_URL` |
| Email (with PDF attachment) | `SMTP_*`, `NOTIFY_EMAIL_TO` |

---

## Target environment: zyvor.dev

[zyvor.dev](https://zyvor.dev) is the **marketing site** — no dashboard login flow.

```bash
ZYVOR_BASE_URL=https://zyvor.dev
# ENABLE_DASHBOARD_TESTS=false   # default
```

Do not set `ZYVOR_STAGING_URL` or test credentials unless you have a real dashboard and set `ENABLE_DASHBOARD_TESTS=true`.

---

## Common errors

| Error | Fix |
|-------|-----|
| `GitHub token required` | Run `gh auth login` or set `GITHUB_TOKEN` in `.env` |
| `ZYVOR_PRODUCT_REPO is not set` | Add `owner/repo` to `.env` |
| `Failed to fetch spec from GitHub` | Check file path exists in the repo; verify token has `Contents: Read` |
| `No requirements extracted from specs` | Add acceptance criteria to the markdown file |
| `gh auth token` invalid | Run `gh auth refresh -h github.com` |

---

## Related files

| File | Purpose |
|------|---------|
| `orchestrator/cli.py` | CLI commands |
| `orchestrator/nodes/fetch.py` | Local vs GitHub spec fetching |
| `orchestrator/nodes/discover.py` | Coverage inventory discovery |
| `orchestrator/nodes/gap_analyze.py` | Gap analysis vs existing tests |
| `agents/discover/agent.py` | Heuristic extractors for routes/pages/docs |
| `agents/coverage/gap.py` | Gap matching and requirement conversion |
| `github_integration/client.py` | GitHub API, token resolution, file download |
| `agents/parser/agent.py` | Spec → requirements |
| `agents/generator/agent.py` | Requirements → Playwright tests |
| `templates/test.spec.ts.j2` | Template fallback for generation |
| `prompts/examples/vm-create.md` | Example spec |
| `.env.example` | All environment variables |
