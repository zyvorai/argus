# Pipedrive CRM pack

Point Argus at a **Pipedrive company sandbox** you control.

Hands-on walkthrough: [Tutorial 19 — Test a CRM](../tutorials/19-crm-golden-paths.md).

## Env

```bash
export ZYVOR_BASE_URL=https://app.pipedrive.com
export PIPEDRIVE_USER='you@example.com'
export PIPEDRIVE_PASS='…'
# Settings → Personal preferences → API → Personal API token
export PIPEDRIVE_TOKEN='…'
# Optional company subdomain if you use one:
# export ZYVOR_BASE_URL=https://your-company.pipedrive.com
```

Disable MFA on the sandbox user for v1.

## CLI

```bash
# 1) Auth
argus api auth-test "$ZYVOR_BASE_URL" \
  --login-url /auth/login \
  --username "$PIPEDRIVE_USER" --password "$PIPEDRIVE_PASS" \
  --protected /pipeline

# 2) UI journey
argus flow run "$ZYVOR_BASE_URL" \
  --steps docs/assets/crm/pipedrive-demo.steps \
  --session app.pipedrive.com --video

# 3) REST deals / persons (Bearer — works for OAuth access tokens;
#    personal API tokens: if you get 401, append ?api_token=$PIPEDRIVE_TOKEN to each path)
argus api test "https://api.pipedrive.com" \
  --workflow docs/assets/crm/pipedrive-deals.workflow.json \
  --token "$PIPEDRIVE_TOKEN"

# 4) Route sweep — paths from pipedrive-routes.txt
```

## Mission Control

1. **Auth & session** — login `/auth/login` (or your portal’s login path), protected `/pipeline`.
2. **Flow test** — [`pipedrive-demo.steps`](../assets/crm/pipedrive-demo.steps), session `app.pipedrive.com`.
3. **API contract** — base `https://api.pipedrive.com`, workflow [`pipedrive-deals.workflow.json`](../assets/crm/pipedrive-deals.workflow.json).
4. **Route sweep** — [`pipedrive-routes.txt`](../assets/crm/pipedrive-routes.txt).

## Assets

| File | Role |
|------|------|
| [`pipedrive-demo.steps`](../assets/crm/pipedrive-demo.steps) | Pipeline / deals → open deal |
| [`pipedrive-deals.workflow.json`](../assets/crm/pipedrive-deals.workflow.json) | List deals + persons |
| [`pipedrive-routes.txt`](../assets/crm/pipedrive-routes.txt) | Route sweep paths |
| [`crm-pipedrive.md`](../../prompts/examples/crm-pipedrive.md) | Spec for `argus test generate` |

## Notes

- Login URL and deal list labels change with Pipedrive UI updates — tweak asserts if needed.
- Prefer read-only API steps in shared sandboxes; add POST only when you own the company.
