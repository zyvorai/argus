# HubSpot CRM pack

Point Argus at a **HubSpot sandbox / developer account** you control.

Hands-on walkthrough: [Tutorial 19 — Test a CRM](../tutorials/19-crm-golden-paths.md).

## Env

```bash
export ZYVOR_BASE_URL=https://app.hubspot.com
export HUBSPOT_USER='you@example.com'
export HUBSPOT_PASS='…'
# Private app token (Settings → Integrations → Private Apps)
export HUBSPOT_TOKEN='pat-…'
```

Disable MFA on the sandbox user for v1 (these packs do not drive OTP).

## CLI

```bash
# 1) Auth — saves reports/artifacts/auth/app.hubspot.com.json
argus api auth-test "$ZYVOR_BASE_URL" \
  --login-url /login \
  --username "$HUBSPOT_USER" --password "$HUBSPOT_PASS" \
  --protected /contacts

# 2) UI journey (reuse session)
argus flow run "$ZYVOR_BASE_URL" \
  --steps docs/assets/crm/hubspot-demo.steps \
  --session app.hubspot.com --video

# 3) REST contacts
argus api test https://api.hubapi.com \
  --workflow docs/assets/crm/hubspot-contacts.workflow.json \
  --token "$HUBSPOT_TOKEN"

# 4) Visual sweep (CLI has no --session; use Mission Control Route sweep
#    with a saved session when the CRM requires login)
argus vision route-sweep "$ZYVOR_BASE_URL" \
  --routes /contacts,/contacts/objects/0-1,/deals,/companies
```

## Mission Control

1. **API** → **Auth & session** — URL `https://app.hubspot.com`, login `/login`, username/password, protected `/contacts`.
2. **Journeys** → **Flow test** — paste [`hubspot-demo.steps`](../assets/crm/hubspot-demo.steps), reuse session `app.hubspot.com`, record video.
3. **API** → **API contract** — base `https://api.hubapi.com`, workflow file [`hubspot-contacts.workflow.json`](../assets/crm/hubspot-contacts.workflow.json), bearer = private app token.
4. **Visual** → **Route sweep** — routes from [`hubspot-routes.txt`](../assets/crm/hubspot-routes.txt).

## Assets

| File | Role |
|------|------|
| [`hubspot-demo.steps`](../assets/crm/hubspot-demo.steps) | Contacts list → open record |
| [`hubspot-contacts.workflow.json`](../assets/crm/hubspot-contacts.workflow.json) | List + optional create contact |
| [`hubspot-routes.txt`](../assets/crm/hubspot-routes.txt) | Route sweep paths |
| [`crm-hubspot.md`](../../prompts/examples/crm-hubspot.md) | Spec for `argus test generate` |

## Notes

- UI paths (`/contacts`, object ids) vary by HubSpot portal; adjust steps if the first assert fails.
- Prefer API create over UI create so sandboxes stay tidy and selectors stay stable.
- The contacts workflow POSTs `argus-qa-sandbox@example.com` — change that email or delete the contact between runs to avoid HubSpot 409 conflicts.
- Step 2 (read first contact) needs at least one existing contact; empty portals can skip that step or seed one contact first.
