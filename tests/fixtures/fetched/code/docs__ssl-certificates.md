---
sidebar_position: 11
title: SSL/TLS Certificates
description: Managing SSL certificates for zyvor.dev (and related hostnames)
---

# SSL/TLS Certificate Management

## Current Certificate

| Field | Value |
|-------|-------|
| **Domain** | **`www.zyvor.dev` + `zyvor.dev` (SAN)** |
| **CA** | Sectigo (via ClickSSL / PositiveSSL DV) |
| **CA Order** | `2966406867` |
| **Valid Until** | 2026-10-26 |
| **Key Type** | RSA |
| **Validation** | FILE (HTTP DCV) |

## File Locations

### In the project (`ssl/`)

| File | Description |
|------|-------------|
| `ssl/fullchain.crt` | Combined chain (server + intermediates + root) |
| `ssl/leaf.crt` | Server leaf certificate (before building full chain) |
| `*.zip` | Vendor zip from CA (extract into `ssl/`) |
| `ssl/README.md` | Detailed cert info and renewal steps |

### On the server (paths vary by install)

| File | Path |
|------|------|
| **Private Key** | `/etc/ssl/hypersdk/zyvor.dev.key` (example path) |
| **CSR** | `/etc/ssl/hypersdk/zyvor.dev.csr` |

The private key is **not** included in the distribution.

## How Deployment Works

The deploy script handles SSL automatically:

```bash
REMOTE_USER=sus ./scripts/deploy.sh YOUR_SERVER_IP
```

1. **Preferred:** `ssl/fullchain.crt` + private key from `bigrock-ssl/` (or `SSL_KEY=...`).
2. **No laptop key:** Deploy falls back to TLS material on the server (`tls-remote-discover.sh` where applicable).
3. **`USE_SERVER_TLS=1`:** Always use server TLS only (do not upload local fullchain even if present).

See `ssl/README.md`.

## DCV Validation

The Domain Control Validation file is at:

```
static/.well-known/pki-validation/7B0417071935E3110C64D313E9BFCE9F.txt
```

The website edge server serves `.well-known/` over HTTP (no HTTPS redirect) so the CA can validate:

```nginx
location /.well-known/ {
    root /usr/share/nginx/html;
}
```

## Certificate Renewal

When the certificate expires (2026-10-26):

1. Order a new certificate from ClickSSL (same domain, same or new CSR)
2. If new CSR needed:
   ```bash
   ssh sus@YOUR_SERVER_IP
   sudo openssl req -new -newkey rsa:4096 -nodes \
     -keyout /etc/ssl/hypersdk/zyvor.dev.key \
     -out /etc/ssl/hypersdk/zyvor.dev.csr \
     -subj '/CN=www.zyvor.dev'
   cat /etc/ssl/hypersdk/zyvor.dev.csr
   ```
3. Place the new DCV file in `static/.well-known/pki-validation/`
4. Deploy to make it accessible: `REMOTE_USER=sus ./scripts/deploy.sh YOUR_SERVER_IP`
5. Complete FILE validation on the ClickSSL portal
6. Download the new certificate zip
7. Extract and rebuild the fullchain (CA-issued PEMs only):
   ```bash
   cd ssl/
   unzip -o your-ca-bundle.zip
   ./scripts/build-fullchain.sh
   ```
   On renewal, intermediate filenames may change — update `scripts/build-fullchain.sh` if the CA ships different PEM names. Order is always: **leaf, then intermediates, then root**.
8. Redeploy: `REMOTE_USER=sus ./scripts/deploy.sh YOUR_SERVER_IP`
9. Verify:
   ```bash
   echo | openssl s_client -connect zyvor.dev:443 -servername zyvor.dev 2>/dev/null \
     | openssl x509 -noout -subject -issuer -dates
   ```

## hypersdk.cloud (santiago profile)

TLS material lives in **`santiago-ssl/`** (gitignored). One-command container deploy:

```bash
REMOTE_USER=sus ./scripts/deploy-container.sh YOUR_SERVER_IP sus santiago
# or: make deploy-hypersdk-cloud SERVER=YOUR_SERVER_IP REMOTE_USER=sus
```

This automatically:
1. Builds with `SITE_URL=https://hypersdk.cloud`
2. Resolves `santiago-ssl/fullchain.crt` + matching key (or server TLS under `/etc/ssl/hypersdk/`)
3. Verifies the leaf SAN names `hypersdk.cloud`
4. Stops systemd nginx if it holds ports 80/443, then starts the podman container

See `santiago-ssl/README.md` in the hypersdk-web repository (TLS bundle is gitignored and not linked from the public docs site). Host `YOUR_SERVER_IP` remains zyvor.dev / `bigrock-ssl/` only.

## Server Details

- **IP**: YOUR_SERVER_IP
- **OS**: AlmaLinux 9
- **Container Runtime**: Podman (rootful)
- **Web Server**: `website-server` (inside container)
- **Network Mode**: `--network host`
