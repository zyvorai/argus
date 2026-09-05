# zyvor.dev on your server

Point **`zyvor.dev`** at your web server IP (**e.g. `YOUR_SERVER_IP`**) and serve the same marketing site (or a dedicated build) with HTTPS.

## Security: private keys

- **Never commit** TLS private keys or paste them into tickets, chat, or CI logs.
- If a key was exposed, **revoke and reissue** the certificate (Let's Encrypt: `certbot revoke` then obtain a new cert, or use your CA’s reissue flow).

On the server, key material should live only under **`/etc/nginx/ssl/`** (or `/etc/letsencrypt/`) with restrictive permissions (`chmod 600` on keys).

## DNS

At your domain registrar / DNS host:

| Type | Name | Value           | TTL |
|------|------|-----------------|-----|
| A    | `@` (or `zyvor.dev`) | `YOUR_SERVER_IP` | 300–3600 |
| A    | `www` | `YOUR_SERVER_IP` (optional) | same |

Wait for DNS to propagate before testing HTTPS. The IP **`OTHER_PANEL_IP`** (if shown in a control panel) is unrelated to this A record unless you intentionally use it—visitors resolve whatever your **public A record** returns.

## TLS certificate files

After you have a valid certificate for **`zyvor.dev`** and **`www.zyvor.dev`** (or a wildcard `*.zyvor.dev`), install:

| File on server | Purpose |
|----------------|---------|
| `/etc/nginx/ssl/zyvor.fullchain.crt` | Leaf + intermediate chain (PEM) |
| `/etc/nginx/ssl/zyvor.key` | Private key (matches the certificate) |

Example from Certbot (paths may vary):

```bash
sudo install -m 644 /etc/letsencrypt/live/zyvor.dev/fullchain.pem /etc/nginx/ssl/zyvor.fullchain.crt
sudo install -m 600 /etc/letsencrypt/live/zyvor.dev/privkey.pem   /etc/nginx/ssl/zyvor.key
```

## Nginx

1. Copy [`nginx/zyvor-dev.conf`](../nginx/zyvor-dev.conf) to the server:

   ```bash
   sudo cp zyvor-dev.conf /etc/nginx/conf.d/zyvor-dev.conf
   ```

2. Ensure the static root exists (same as main site, default **`/var/www/hypersdk`**).

3. Test and reload:

   ```bash
   sudo nginx -t && sudo systemctl reload nginx
   ```

4. Verify from your laptop:

   ```bash
   curl -sSI https://zyvor.dev
   echo | openssl s_client -connect zyvor.dev:443 -servername zyvor.dev 2>/dev/null | openssl x509 -noout -subject -issuer -dates
   ```

## Same repo, two domains

This vhost reuses **`root /var/www/hypersdk`** for **zyvor.dev**. To use a separate tree, change `root` in `zyvor-dev.conf` and deploy there.

## Automation

After **`/etc/nginx/ssl/zyvor.fullchain.crt`** and **`zyvor.key`** exist on the server, bare deploys can install the vhost automatically:

```bash
DEPLOY_ZYVOR_NGINX=1 ./scripts/deploy.sh user@YOUR_SERVER_IP --bare
# or
DEPLOY_ZYVOR_NGINX=1 ./scripts/deploy-all.sh YOUR_SERVER_IP
```

If those TLS files are missing, the script exits with an error instead of breaking `nginx -t`.

## Verify configs locally

```bash
chmod +x scripts/verify-nginx-confs.sh
./scripts/verify-nginx-confs.sh
```

Uses Docker (`nginx:alpine`) when available, else system `nginx -t`.
