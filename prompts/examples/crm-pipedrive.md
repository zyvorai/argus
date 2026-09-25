# Operator opens Pipedrive deals — sandbox validation

**As a** sales operator
**I want to** open the Pipedrive pipeline and a deal record
**So that** I can trust the CRM UI after a deploy or config change

## Acceptance Criteria

1. Authenticated session reaches `/pipeline`
2. Deals list loads with visible list chrome
3. Opening a deal shows Person (or equivalent detail field)
4. API `GET /v1/deals` with `api_token` returns 200

## Environment

- UI: `ZYVOR_BASE_URL=https://app.pipedrive.com` (or company subdomain)
- API: `https://api.pipedrive.com` with `PIPEDRIVE_TOKEN`
- Company sandbox only; no MFA on the test user

## Tags

crm, pipedrive, smoke, deals
