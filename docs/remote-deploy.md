# Remote Deployment (`scripts/deploy-remote.sh`)

One SSH+rsync script deploys the agent — and its live [Mission Control dashboard](tutorials/10-mission-control-dashboard.md) — to any host, in four profiles.

```bash
./scripts/deploy-remote.sh <host> <user> [options]
./scripts/deploy-remote.sh user@host [options]
./scripts/deploy-remote.sh --fleet hosts.txt
```

## Profiles

| Profile | Flag | What it does |
|---------|------|--------------|
| 🏗️ Full | *(default)* | System deps → Python venv + `argus` CLI → npm + Playwright Chromium → verify |
| ⚡ Quick | `--quick` | Rsync + reinstall Python/Node deps (skip system packages) — fast redeploys |
| 🐳 Container | `--container` | Build `docker/Dockerfile` on the remote (Docker **or** Podman, auto-detected) and run it |
| ☸️ Kubernetes | `--k3s` | Install k3s, build + import the image under a content-unique tag, apply `kubernetes/` (webhook pod, RBAC, nightly CronJob), expose a NodePort |

## Common options

| Option | Effect |
|--------|--------|
| `--service` | Install + (re)start a systemd unit for `argus serve` (full/quick/container profiles) |
| `--port N` | Serve port (default **30080**, fixed and persisted per host; reused on redeploys) |
| `--runtime docker\|podman` / `--podman` | Force a container runtime (default: auto-detect, install per package manager) |
| `--no-auth` | Skip dashboard login setup |
| `--smoke` | Run `argus test exec` on the remote after deploy |
| `--with-env` | Also rsync the local `.env` (secrets — excluded by default) |
| `--dry-run` · `--preflight-only` · `--verify-only` · `--skip-sync` · `--skip-verify` | Inspection / partial runs |
| `--uninstall` | Remove the service, container, and k8s resources |

## Login

Dashboard auth is on by default. Credentials default to **`admin` / `Admin@321`**, persisted per host in `~/.deployments/zyvor-argus/.zyvor-argus-auth`, written into the remote `.env` and (on k3s) the Secret, and printed in the deploy summary. Override with `ZYVOR_ARGUS_DASH_USER` / `ZYVOR_ARGUS_DASH_PASS`, or `--no-auth` to disable.

## Examples

```bash
./scripts/deploy-remote.sh 10.0.0.5 operator                 # full bare-host + dashboard
./scripts/deploy-remote.sh 10.0.0.5 operator --quick --service   # fast redeploy, systemd service
./scripts/deploy-remote.sh 10.0.0.5 operator --container --podman # container via Podman
./scripts/deploy-remote.sh 10.0.0.5 operator --k3s               # k3s + pods + NodePort
./scripts/deploy-remote.sh 10.0.0.5 operator --service --port 8090  # serve on a free port
```

Then open `http://<host>:<port>/dashboard` (or `kubectl port-forward` for k3s) and sign in.

## Notes & gotchas

- **State files** (`.zyvor-argus-port`, `.zyvor-argus-auth`, `.zyvor-argus-image-tag`) live under the remote deploy dir and are protected from `rsync --delete`, so the port, login, and image stay stable across redeploys.
- **Port already in use / dashboard 404s?** The host likely already runs k3s (or another service) on that NodePort — deploy on a free `--port`, or use the `--k3s` profile so the app runs as a pod behind the NodePort.
- **k3s image freshness:** each `--k3s` deploy imports the image under a unique tag (`zyvor-argus:d<timestamp>`) so containerd can't dedupe to stale code.
- A **fleet file** runs the same deploy across many hosts, one per line: `host user [password] [options]`.
