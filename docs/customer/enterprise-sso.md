# Enterprise SSO / OIDC (Keycloak)

How to sign into **Argus Enterprise** (Watchfloor) after install: bundled
Keycloak, your own OIDC provider, or a local username/password for a test lab.

This chapter is for the **Argus Enterprise** customer package (Helm chart +
scripts). Community Mission Control (`argus serve`) still uses
`DASHBOARD_PASSWORD` — see [Admin basics](admin-basics.md).

## Demo accounts (smoke-test only)

After a default install with bundled Keycloak and test users enabled:

| Username | Password | Purpose |
|----------|----------|---------|
| `demo` | `demo` | Quick manual login check |
| `ssouser` | `Sso@321` | Scripted / `test-login.sh` smoke test |

**These are not production accounts.** Disable them for a real customer
environment (`keycloak.createTestUsers: false` in Helm, or delete the users
in Keycloak after you verify login).

```bash
scripts/test-login.sh https://argus.example.com demo demo
# or
scripts/test-login.sh https://argus.example.com ssouser 'Sso@321'
```

## Option A — Helm with bundled Keycloak (recommended)

```bash
# Load the image from the customer package first (see that package's INSTALL.md), then:
helm install argus charts/argus-enterprise-*.tgz \
  --set appUrl=https://argus.example.com \
  --set keycloak.externalUrl=https://sso.example.com \
  --set keycloak.ingress.enabled=true \
  --set keycloak.ingress.className=<your-ingress-class> \
  --set keycloak.ingress.host=sso.example.com
```

What this does:

- Deploys the app, Postgres, and Keycloak.
- A post-install Job creates the `argus` realm, the `argus-enterprise` OIDC
  client, and (by default) the `demo` / `ssouser` test users above.
- Secrets (Postgres password, Keycloak admin password, OIDC client secret)
  are generated once and kept stable across `helm upgrade`.

Required values (no safe default):

- `appUrl` — browser-reachable URL of the app
- `keycloak.externalUrl` — browser-reachable URL of Keycloak

Keycloak must be reachable from browsers via **Ingress** (`keycloak.ingress.*`)
or a **NodePort** (`keycloak.nodePort`). The chart fails install if neither
is set.

After pods are ready:

1. Read the one-time owner setup token from app logs:
   `kubectl logs -n <ns> deploy/argus | grep -A3 -i "one-time"`
2. Open `appUrl`, claim ownership with your email + that token.
3. On the login screen, pick the SSO / Keycloak provider and sign in with
   `demo` / `demo` (or `ssouser` / `Sso@321`) to confirm OIDC.

Turn off test users for production:

```bash
helm upgrade argus charts/argus-enterprise-*.tgz \
  --reuse-values \
  --set keycloak.createTestUsers=false
```

(Also delete any already-created `demo` / `ssouser` users in the Keycloak
admin console if they remain.)

## Option B — Bring your own OIDC provider

Okta, Azure AD, Google Workspace, an existing Keycloak, or any standards-
compliant OIDC IdP:

```bash
helm install argus charts/argus-enterprise-*.tgz \
  --set appUrl=https://argus.example.com \
  --set keycloak.enabled=false \
  --set oidc.issuer=https://login.example.com/realms/your-realm \
  --set oidc.clientId=argus-enterprise \
  --set oidc.clientSecret=<secret>
```

Register this redirect URI on your IdP:

```text
https://argus.example.com/api/enterprise/auth/callback/default
```

Demo Keycloak users do **not** apply here — use accounts from your IdP.

## Option C — Local username/password (test lab, no IdP)

When you have nowhere to run Keycloak and no external IdP:

```bash
helm install argus charts/argus-enterprise-*.tgz \
  --set appUrl=https://argus.example.com \
  --set keycloak.enabled=false \
  --set localAuth.enabled=true
```

1. Claim the deployment with email + setup token **and** a password
   (the claim form shows a password field when local auth is on).
2. That password becomes the owner's login.
3. Owners can add more local accounts later via `POST /admin/local-accounts`.

Local auth and SSO can run together: the login screen shows both when both
are configured. Prefer real SSO for any production deployment.

## Option D — Manual / plain Docker (no Helm)

From the Enterprise package:

1. **Deploy Keycloak** (skip if you already have an OIDC provider):

   ```bash
   kubectl create namespace argus-enterprise
   kubectl create secret generic argus-keycloak-admin -n argus-enterprise \
     --from-literal=password="$(openssl rand -hex 20)"
   kubectl apply -f k8s/keycloak-theme-configmap.yaml
   kubectl apply -f k8s/sso-keycloak.yaml
   ```

2. **Create a client secret** and provision realm + test users:

   ```bash
   CLIENT_SECRET="$(openssl rand -hex 32)"
   KEYCLOAK_ADMIN_PASSWORD="<password from step 1>" \
     scripts/keycloak-bootstrap.sh <k8s-host> <ssh-user> "$CLIENT_SECRET" http://<app-host>:8090
   ```

   This creates `ssouser`/`Sso@321` and `demo`/`demo`. Re-run after any
   Keycloak pod restart if you use the ephemeral `start-dev` manifest
   (`k8s/sso-keycloak.yaml`) — a restart wipes the realm.

3. **Deploy the app** wired to that client:

   ```bash
   DEPLOY_OIDC_ISSUER="http://<keycloak-host>:30180/realms/argus" \
   DEPLOY_OIDC_CLIENT_ID="argus-enterprise" \
   DEPLOY_OIDC_CLIENT_SECRET="$CLIENT_SECRET" \
   DEPLOY_EXTRA_ENV="ARGUS_ENTERPRISE_DB_URL=postgresql+psycopg://user:pass@host/db,ARGUS_ENTERPRISE_SESSION_SECRET=$(openssl rand -hex 32)" \
     scripts/deploy-remote.sh <app-host> <ssh-user>
   ```

4. **Claim** via the one-time token in `docker logs`, then log in with
   `demo` / `demo`.

Keep the same `$CLIENT_SECRET` for Keycloak and the app. If they drift,
login fails with a generic OAuth error — re-run bootstrap with the same
secret.

For local auth only (no Keycloak):

```bash
DEPLOY_EXTRA_ENV=ARGUS_ENTERPRISE_LOCAL_AUTH_ENABLED=true \
  scripts/deploy-remote.sh <app-host> <ssh-user>
```

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| SSO button missing | No IdP registered / OIDC env not set | Check Helm `oidc.*` or `DEPLOY_OIDC_*`; claim as owner and register an IdP if using the admin API |
| Login loops / generic OAuth error | Client secret mismatch | Re-run `keycloak-bootstrap.sh` with the **same** secret the app has |
| SSO worked, then broke after Keycloak restart | Ephemeral Keycloak storage wiped the realm | Re-run `keycloak-bootstrap.sh` (or let the Helm post-upgrade Job re-provision) |
| User created but can't finish login | Keycloak `VERIFY_PROFILE` wants first/last name | Use `keycloak-bootstrap.sh` / the Helm Job (they set names); or fill profile in Keycloak |
| Need a login with no IdP | Local auth off | `--set localAuth.enabled=true` or `ARGUS_ENTERPRISE_LOCAL_AUTH_ENABLED=true` |

## Related

- [Admin basics](admin-basics.md) — Mission Control `DASHBOARD_PASSWORD` auth
- [Getting Started](getting-started.md)
- [Login (Mission Control)](pages/overview/login.md)
- Engineering mirror (same content, repo docs tree): [`../enterprise-sso-oidc.md`](../enterprise-sso-oidc.md)
- Sales / managed deploys: [zyvor.dev](https://zyvor.dev) · [sales@zyvor.dev](mailto:sales@zyvor.dev)
