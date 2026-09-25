# Operator opens Salesforce Sales Cloud Accounts — sandbox validation

**As a** sales operator
**I want to** open the Salesforce Accounts list and an account record
**So that** I can trust Sales Cloud after a deploy or config change

## Acceptance Criteria

1. Authenticated Classic session reaches `/001/o` (Accounts)
2. Accounts list loads with visible list chrome
3. Opening an account shows Account detail
4. REST `GET /services/data/v59.0/query?q=SELECT+Id,Name+FROM+Account+LIMIT+5` with Bearer token returns 200

## Environment

- UI/API base: `ZYVOR_BASE_URL=https://your-domain.my.salesforce.com` (instance URL)
- Bearer: `SALESFORCE_TOKEN` (OAuth access token or session ID)
- Developer Edition / sandbox only; Classic UI for flows; no MFA on the test user
- Lightning Experience is out of scope for the committed `.steps` file

## Tags

crm, salesforce, sales-cloud, smoke, accounts
