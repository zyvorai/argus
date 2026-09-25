# Operator opens Zoho CRM leads — sandbox validation

**As a** CRM operator
**I want to** open the Zoho CRM Leads module and a lead record
**So that** I can trust the CRM UI after a deploy or config change

## Acceptance Criteria

1. Authenticated session reaches `/crm/tab/Leads`
2. Leads list loads with visible list chrome
3. Opening a lead shows Email (or equivalent detail field)
4. API `GET /crm/v2/Leads` with OAuth bearer returns 200

## Environment

- UI: `ZYVOR_BASE_URL=https://crm.zoho.com` (or `.eu` / `.in` / …)
- API: `https://www.zohoapis.com` (matching DC) with `ZOHO_TOKEN`
- Sandbox / trial only; no MFA on the test user; OAuth token issued outside Argus

## Tags

crm, zoho, smoke, leads
