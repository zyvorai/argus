# Salesforce Sales Cloud pack (UI-first)

Point Argus at a **Salesforce Developer Edition / sandbox** with **username + password only**.
No API token is required for the primary recipe.

**Classic** is the committed flow path (more Playwright-friendly). Lightning Experience uses shadow DOM — use Import codegen instead of the hand steps below.

## Will this run?

1. Sandbox / DE user with **MFA off**
2. Correct **My Domain** URL
3. User switched to **Salesforce Classic** (or Classic as default)
4. At least one **Account** so open-record has a target
5. Run auth → flow → route sweep; tweak one `click`/`assert` if labels differ

## Env

```bash
export ZYVOR_BASE_URL=https://your-domain.my.salesforce.com
export SALESFORCE_USER='you@example.com'
export SALESFORCE_PASS='…'
```

## CLI (primary — Classic UI only)

```bash
# Switch to Classic in the browser once before capturing a session.

# 1) Auth
argus api auth-test "$ZYVOR_BASE_URL" \
  --login-url / \
  --username "$SALESFORCE_USER" --password "$SALESFORCE_PASS" \
  --protected /001/o

# 2) UI journey (Classic Accounts)
argus flow run "$ZYVOR_BASE_URL" \
  --steps docs/assets/crm/salesforce-demo.steps \
  --session your-domain.my.salesforce.com --video

# 3) Route sweep — Classic tabs (Mission Control when session required)
#    Paths: see salesforce-routes.txt
```

Adjust `--session` to the basename under `reports/artifacts/auth/`.

## Mission Control

1. **Auth & session** — My Domain URL, login `/`, protected `/001/o`. Confirm Classic before starting.
2. **Flow test** — [`salesforce-demo.steps`](../assets/crm/salesforce-demo.steps), reuse session, record video.
3. **Route sweep** — [`salesforce-routes.txt`](../assets/crm/salesforce-routes.txt).

## Lightning (codegen, not hand steps)

1. Log into Lightning in a normal browser.
2. Mission Control → **Import codegen** (or `node playwright/scripts/record-flow.mjs`) against `/lightning/o/Account/list`.
3. Save the generated steps and run them with Flow test + the same session.
   Do **not** expect [`salesforce-demo.steps`](../assets/crm/salesforce-demo.steps) to pass under Lightning.

## Assets

| File | Role |
|------|------|
| [`salesforce-demo.steps`](../assets/crm/salesforce-demo.steps) | Classic Accounts → open record |
| [`salesforce-routes.txt`](../assets/crm/salesforce-routes.txt) | Classic tab paths |
| [`salesforce-accounts.workflow.json`](../assets/crm/salesforce-accounts.workflow.json) | Optional API (see below) |
| [`crm-salesforce.md`](../../prompts/examples/crm-salesforce.md) | Spec for `argus test generate` |

## Optional (when you have a token)

```bash
export SALESFORCE_TOKEN='00D…!…'   # OAuth access token / session ID

argus api test "$ZYVOR_BASE_URL" \
  --workflow docs/assets/crm/salesforce-accounts.workflow.json \
  --token "$SALESFORCE_TOKEN"
```

Bump `v59.0` in the workflow if `GET /services/data/` lists a different version.

## Notes

- Auth-probe prefers `#username` / `#password` / `#Login` on My Domain / login.salesforce.com.
- SSO/SAML and MFA are out of scope for this pack.
