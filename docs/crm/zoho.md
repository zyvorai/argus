# Zoho CRM pack

Point Argus at a **Zoho CRM sandbox / trial** you control. Fits teams already on Zoho (mail, CRM).

## Env

```bash
export ZYVOR_BASE_URL=https://crm.zoho.com
# EU / IN / AU / JP data centres use crm.zoho.eu, crm.zoho.in, …
export ZOHO_USER='you@example.com'
export ZOHO_PASS='…'
# OAuth access token (or self-client) with ZohoCRM.modules.READ
export ZOHO_TOKEN='1000.…'
# API host must match the data centre:
export ZOHO_API_BASE=https://www.zohoapis.com
# EU example: https://www.zohoapis.eu
```

Disable MFA on the sandbox user for v1. Prefer a pre-issued OAuth token over interactive Zoho OAuth in the browser.

## CLI

```bash
# 1) Auth (password login — skip if you only use API packs)
argus api auth-test "$ZYVOR_BASE_URL" \
  --login-url /crm/login.do \
  --username "$ZOHO_USER" --password "$ZOHO_PASS" \
  --protected /crm/tab/Leads

# 2) UI journey
argus flow run "$ZYVOR_BASE_URL" \
  --steps docs/assets/crm/zoho-demo.steps \
  --session crm.zoho.com --video

# 3) REST Leads
argus api test "$ZOHO_API_BASE" \
  --workflow docs/assets/crm/zoho-leads.workflow.json \
  --token "$ZOHO_TOKEN"

# 4) Route sweep — paths from zoho-routes.txt
```

## Mission Control

1. **Auth & session** — login path for your DC, protected `/crm/tab/Leads`.
2. **Flow test** — [`zoho-demo.steps`](../assets/crm/zoho-demo.steps), session `crm.zoho.com` (or your DC host).
3. **API contract** — base `$ZOHO_API_BASE`, workflow [`zoho-leads.workflow.json`](../assets/crm/zoho-leads.workflow.json), bearer = OAuth access token.
4. **Route sweep** — [`zoho-routes.txt`](../assets/crm/zoho-routes.txt).

## Assets

| File | Role |
|------|------|
| [`zoho-demo.steps`](../assets/crm/zoho-demo.steps) | Leads list → open lead |
| [`zoho-leads.workflow.json`](../assets/crm/zoho-leads.workflow.json) | List + read Leads |
| [`zoho-routes.txt`](../assets/crm/zoho-routes.txt) | Route sweep paths |
| [`crm-zoho.md`](../../prompts/examples/crm-zoho.md) | Spec for `argus test generate` |

## Notes

- Zoho UI paths differ by edition (CRM Plus vs standard) and data centre — adjust `goto` targets if asserts fail.
- Refresh OAuth tokens outside Argus; these packs do not run the Zoho OAuth dance.
