# Salesforce Sales Cloud pack

Point Argus at a **Salesforce Developer Edition / sandbox** you control.
**API-first** (REST + SOQL) is the reliable path. UI steps target **Salesforce Classic** list URLs — Lightning Experience uses shadow DOM and is not the documented path (use [Import codegen](../user/pages/journeys/dashboard-actions-import-codegen.md) if you must drive Lightning).

## Env

```bash
# My Domain / instance URL from the OAuth token response (instance_url)
export ZYVOR_BASE_URL=https://your-domain.my.salesforce.com
export SALESFORCE_USER='you@example.com'
export SALESFORCE_PASS='…'
# OAuth access token or session ID (Bearer). Issue outside Argus:
# Connected App + password grant, or paste from Workbench / CLI.
export SALESFORCE_TOKEN='00D…!…'
```

Disable MFA on the sandbox user for UI auth. Prefer a pre-issued access token for API-only runs.

## CLI

```bash
# 1) Auth (Classic UI session — skip if you only run the API workflow)
argus api auth-test "$ZYVOR_BASE_URL" \
  --login-url / \
  --username "$SALESFORCE_USER" --password "$SALESFORCE_PASS" \
  --protected /001/o

# 2) UI journey (Classic Accounts tab)
argus flow run "$ZYVOR_BASE_URL" \
  --steps docs/assets/crm/salesforce-demo.steps \
  --session your-domain.my.salesforce.com --video

# 3) REST Accounts (Bearer = access token)
argus api test "$ZYVOR_BASE_URL" \
  --workflow docs/assets/crm/salesforce-accounts.workflow.json \
  --token "$SALESFORCE_TOKEN"

# 4) Visual sweep — Classic tabs from salesforce-routes.txt
#    (CLI has no --session; use Mission Control Route sweep when login is required)
argus vision route-sweep "$ZYVOR_BASE_URL" \
  --routes /home/home.jsp,/001/o,/003/o,/006/o,/00Q/o
```

Session file names follow the auth host (e.g. `your-domain.my.salesforce.com`). Adjust `--session` to match `reports/artifacts/auth/<host>.json`.

## Mission Control

1. **API** → **Auth & session** — My Domain URL, protected `/001/o` (Accounts). Switch the user to **Salesforce Classic** first.
2. **Journeys** → **Flow test** — paste [`salesforce-demo.steps`](../assets/crm/salesforce-demo.steps), reuse the saved session, record video.
3. **API** → **API contract** — base = instance URL, workflow [`salesforce-accounts.workflow.json`](../assets/crm/salesforce-accounts.workflow.json), bearer = `SALESFORCE_TOKEN`.
4. **Visual** → **Route sweep** — routes from [`salesforce-routes.txt`](../assets/crm/salesforce-routes.txt).

## Assets

| File | Role |
|------|------|
| [`salesforce-demo.steps`](../assets/crm/salesforce-demo.steps) | Classic Accounts list → open record |
| [`salesforce-accounts.workflow.json`](../assets/crm/salesforce-accounts.workflow.json) | API versions + SOQL Accounts + read |
| [`salesforce-routes.txt`](../assets/crm/salesforce-routes.txt) | Classic tab paths |
| [`crm-salesforce.md`](../../prompts/examples/crm-salesforce.md) | Spec for `argus test generate` |

## Notes

- Bump `v59.0` in the workflow if your org’s available API versions differ (`GET /services/data/`).
- Empty orgs: seed at least one Account before the “read account” step, or remove that step.
- Lightning URLs (`/lightning/o/Account/list`) are unsupported in this pack’s `.steps` file.
- Refresh OAuth tokens outside Argus; packs do not run the Salesforce OAuth / SAML dance.
