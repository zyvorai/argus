# Operator opens Salesforce Sales Cloud Accounts — sandbox validation (UI-first)

**As a** sales operator
**I want to** sign in to Classic and open Accounts
**So that** I can trust Sales Cloud after a deploy or config change

## Acceptance Criteria

1. Form login on My Domain succeeds (MFA off)
2. Authenticated Classic session reaches `/001/o` (Accounts)
3. Accounts list loads with visible list chrome
4. Opening an account shows Account detail

## Environment

- UI: `ZYVOR_BASE_URL=https://your-domain.my.salesforce.com`
- Credentials: `SALESFORCE_USER` / `SALESFORCE_PASS` only (API token optional)
- Developer Edition / sandbox; **Classic** UI for committed steps
- Lightning: use Import codegen (not this spec’s hand steps)

## Tags

crm, salesforce, sales-cloud, smoke, accounts, ui
