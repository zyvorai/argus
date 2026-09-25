# Operator opens Zoho CRM leads — sandbox validation (UI-first)

**As a** CRM operator
**I want to** sign in and open the Zoho CRM Leads module and a lead record
**So that** I can trust the CRM UI after a deploy or config change

## Acceptance Criteria

1. Form login via Zoho Accounts succeeds (MFA off)
2. Authenticated session reaches `/crm/tab/Leads`
3. Leads list loads with visible list chrome
4. Opening a lead shows Email (or equivalent detail field)

## Environment

- UI: `ZYVOR_BASE_URL=https://crm.zoho.com` (or `.eu` / `.in` / …)
- Login: `https://accounts.zoho.<dc>/signin`
- Credentials: `ZOHO_USER` / `ZOHO_PASS` only (API token optional)
- Sandbox / trial; no MFA on the test user

## Tags

crm, zoho, smoke, leads, ui
