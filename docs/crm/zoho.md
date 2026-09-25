# Zoho CRM pack (UI-first)

Point Argus at a **Zoho CRM sandbox / trial** you control using **username + password only**.
No API token is required for the primary recipe.

Hands-on walkthrough: [Tutorial 19 — Test a CRM](../tutorials/19-crm-golden-paths.md).

## Will this run?

1. Sandbox / trial user with **MFA off**
2. Correct data centre (`com` / `eu` / `in` / …)
3. At least one **Lead** so open-record has a target
4. Run auth → flow → route sweep; tweak one `click`/`assert` if labels differ

## Env

```bash
export ZOHO_DC=com   # or eu, in, com.au, jp, …
export ZYVOR_BASE_URL=https://crm.zoho.${ZOHO_DC}
export ZOHO_USER='you@example.com'
export ZOHO_PASS='…'
```

## CLI (primary — UI only)

```bash
ACCOUNTS="https://accounts.zoho.${ZOHO_DC}/signin"
HOST="crm.zoho.${ZOHO_DC}"

# 1) Auth via Zoho Accounts (two-step email → password)
argus api auth-test "$ZYVOR_BASE_URL" \
  --login-url "$ACCOUNTS" \
  --username "$ZOHO_USER" --password "$ZOHO_PASS" \
  --protected /crm/tab/Leads

# 2) UI journey (reuse session — file name matches the Accounts/CRM host)
argus flow run "$ZYVOR_BASE_URL" \
  --steps docs/assets/crm/zoho-demo.steps \
  --session "$HOST" --video

# 3) Route sweep — paste paths from zoho-routes.txt in Mission Control
#    (CLI route-sweep has no --session; use the dashboard card when login is required)
```

Session files land under `reports/artifacts/auth/`. If the saved name differs (cookie host), use that basename for `--session`.

## Mission Control

1. **Auth & session** — base = CRM URL; login URL = `https://accounts.zoho.<dc>/signin`; protected `/crm/tab/Leads`.
2. **Flow test** — paste [`zoho-demo.steps`](../assets/crm/zoho-demo.steps), reuse the saved session, record video.
3. **Route sweep** — routes from [`zoho-routes.txt`](../assets/crm/zoho-routes.txt).

## Assets

| File | Role |
|------|------|
| [`zoho-demo.steps`](../assets/crm/zoho-demo.steps) | Leads list → open lead |
| [`zoho-routes.txt`](../assets/crm/zoho-routes.txt) | Route sweep paths |
| [`zoho-leads.workflow.json`](../assets/crm/zoho-leads.workflow.json) | Optional API (see below) |
| [`crm-zoho.md`](../../prompts/examples/crm-zoho.md) | Spec for `argus test generate` |

## Optional (when you have a token)

```bash
export ZOHO_TOKEN='1000.…'
export ZOHO_API_BASE=https://www.zohoapis.${ZOHO_DC}   # .eu / .in as needed

argus api test "$ZOHO_API_BASE" \
  --workflow docs/assets/crm/zoho-leads.workflow.json \
  --token "$ZOHO_TOKEN"
```

## Notes

- Auth-probe handles Zoho’s email-first login (`#login_id` → Next → `#password`).
- CRM paths differ by edition — adjust `goto` / asserts if the first run fails.
- Do not enable MFA on the test user; SSO/SAML is out of scope for this pack.
