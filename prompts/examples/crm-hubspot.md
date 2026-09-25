# Operator opens HubSpot contacts — sandbox validation

**As a** CRM operator
**I want to** open the HubSpot contacts index and a contact record
**So that** I can trust the CRM UI after a deploy or config change

## Acceptance Criteria

1. Authenticated session reaches `/contacts`
2. Contacts list (object `0-1`) loads with visible list chrome
3. Opening a contact shows Email (or equivalent detail field)
4. Private-app API `GET /crm/v3/objects/contacts` returns 200

## Environment

- UI: `ZYVOR_BASE_URL=https://app.hubspot.com`
- API: `https://api.hubapi.com` with `HUBSPOT_TOKEN`
- Sandbox / developer portal only; no MFA on the test user

## Tags

crm, hubspot, smoke, contacts
