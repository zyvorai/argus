#!/usr/bin/env bash
# Copyright 2026 ZyvorAI Labs Private Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# ─────────────────────────────────────────────────────────────
# Zyvor Argus — Remote deployment (SSH + rsync)
#
# Profiles:
#   default     Sync source → install system deps → venv + npm +
#               Playwright Chromium → /usr/local/bin/argus → verify
#   --quick     Rsync + reinstall Python/Node deps only (skip system deps)
#
# Auth: SSH keys (recommended). Password via sshpass is supported but deprecated.
#
# Post-deploy verify: argus --help + pipeline import check
# ─────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
VERSION="1.0.0"
REMOTE_DIR=""
DEPLOY_PROFILE="full"
DEPLOY_LOG="${ZYVOR_ARGUS_DEPLOY_LOG:-${HOME}/.zyvor-argus/deploy-$(date +%Y%m%d-%H%M%S).log}"

QUICK_MODE=false
UNINSTALL=false
FLEET_FILE=""
KEY_AUTH=false
DRY_RUN=false
SKIP_SYNC=false
SKIP_VERIFY=false
VERIFY_ONLY=false
PREFLIGHT_ONLY=false
WITH_ENV=false
INSTALL_SERVICE=false
TLS_MODE=""
RUN_SMOKE=false
VERBOSE=false
SERVE_PORT="${ZYVOR_ARGUS_PORT:-}"
DEFAULT_SERVE_PORT=30080   # fixed NodePort-range default — stable across hosts and redeploys
RUNTIME_PREF="${ZYVOR_ARGUS_RUNTIME:-}"   # docker | podman | (auto)
NO_AUTH=false
DASH_USER="${ZYVOR_ARGUS_DASH_USER:-admin}"
DASH_PASS_DEFAULT="${ZYVOR_ARGUS_DASH_PASS:-Admin@321}"
DASH_PASS=""
SSH_RETRIES="${ZYVOR_ARGUS_SSH_RETRIES:-3}"
POSITIONAL=()

usage() {
    cat <<EOF
🔧 Zyvor Argus remote deploy v${VERSION}

Usage:
  $0 <host> <user> [options]
  $0 user@host [options]
  $0 --fleet hosts.txt

Profiles:
  🏗️  (default)     Full: system deps (python3, node, chromium libs) + venv + npm
  ⚡  --quick       Rsync + reinstall Python/Node deps (skip system packages)
  🐳  --container   Build image from docker/Dockerfile on the remote and run it
                    (webhook + dashboard served on the random NodePort)
  ☸️  --k3s         Install k3s, build + import the image, deploy kubernetes/
                    manifests (webhook pod, RBAC, nightly CronJob), expose the
                    Service as NodePort on the random port

Options:
  --help              Show this help
  --dry-run           Print steps without SSH/rsync/install
  --preflight-only    SSH + disk/sudo checks, then exit
  --verify-only       Run remote verification only (no deploy)
  --skip-sync         Skip rsync (sources already on host)
  --skip-verify       Skip remote verification
  --with-env          Also sync local .env (contains secrets — default: excluded)
  --service           Install + start systemd unit: argus serve (webhook + dashboard)
  --tls               Serve the dashboard over HTTPS (self-signed cert, auto-generated
                      on the host) — sets the session cookie Secure
  --port N            Serve port (default: 30080 — fixed, NodePort-range,
                      persisted on the remote and reused on redeploys)
  --runtime NAME      Container runtime: docker | podman (default: auto-detect —
                      existing docker, else podman; installs docker on apt hosts
                      and podman on dnf/yum hosts when neither is present)
  --podman            Shorthand for --runtime podman
  --no-auth           Skip dashboard login setup (default: admin / Admin@321,
                      persisted per host; override with ZYVOR_ARGUS_DASH_USER /
                      ZYVOR_ARGUS_DASH_PASS or by editing .zyvor-argus-auth on the host)
  --smoke             Run 'argus test exec' on the remote after deploy
  --key               SSH key auth (clear password)
  --uninstall         Remove argus from host
  -v, --verbose       Verbose rsync

Environment:
  ZYVOR_ARGUS_DEPLOY_LOG    Log file path
  ZYVOR_ARGUS_SSH_RETRIES   SSH retry count (default: 3)
  DEPLOY_DIR             Override remote staging dir (default: ~/.deployments/zyvor-argus)

Examples:
  $0 10.0.0.5 root --key
  $0 sus@10.0.0.5 --quick
  $0 10.0.0.5 root --service --smoke
  $0 10.0.0.5 sus --container                # docker/podman container
  $0 10.0.0.5 sus --container --podman       # force podman
  $0 10.0.0.5 sus --k3s                      # k3s + K8s pods + NodePort
  $0 10.0.0.5 root --verify-only
  make deploy-remote H=10.0.0.5 U=root

Fleet file (one host per line):
  host user [password] [options]
  user@host root --quick
  10.0.0.7 sus --k3s
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        -h|--help)        usage; exit 0 ;;
        --quick)          QUICK_MODE=true; DEPLOY_PROFILE="quick"; shift ;;
        --container)      DEPLOY_PROFILE="container"; shift ;;
        --k3s)            DEPLOY_PROFILE="k3s"; shift ;;
        --tls)            TLS_MODE=true; shift ;;
        --uninstall)      UNINSTALL=true; shift ;;
        --key)            KEY_AUTH=true; shift ;;
        --dry-run)        DRY_RUN=true; shift ;;
        --skip-sync)      SKIP_SYNC=true; shift ;;
        --skip-verify)    SKIP_VERIFY=true; shift ;;
        --with-env)       WITH_ENV=true; shift ;;
        --service)        INSTALL_SERVICE=true; shift ;;
        --port)
            shift
            SERVE_PORT="${1:?--port requires a port number}"
            shift
            ;;
        --runtime)
            shift
            RUNTIME_PREF="${1:?--runtime requires docker or podman}"
            shift
            ;;
        --podman)         RUNTIME_PREF="podman"; shift ;;
        --no-auth)        NO_AUTH=true; shift ;;
        --smoke)          RUN_SMOKE=true; shift ;;
        --verify-only)    VERIFY_ONLY=true; shift ;;
        --preflight-only) PREFLIGHT_ONLY=true; shift ;;
        -v|--verbose)     VERBOSE=true; shift ;;
        --fleet)
            shift
            FLEET_FILE="${1:?--fleet requires a hosts file path}"
            shift
            ;;
        *)
            POSITIONAL+=("$1")
            shift
            ;;
    esac
done

TARGET_HOST="${POSITIONAL[0]:-}"
TARGET_USER="${POSITIONAL[1]:-root}"
TARGET_PASS="${POSITIONAL[2]:-}"

if [ "$KEY_AUTH" = true ]; then
    TARGET_PASS=""
fi

if [[ -n "${TARGET_HOST}" && "${TARGET_HOST}" == *"@"* ]]; then
    TARGET_USER="${TARGET_HOST%%@*}"
    TARGET_HOST="${TARGET_HOST#*@}"
fi

_use_color() { [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; }
if _use_color; then
    C_OK=$'\033[32m'; C_FAIL=$'\033[31m'; C_INFO=$'\033[36m'; C_WARN=$'\033[33m'
    C_DIM=$'\033[2m'; C_BOLD=$'\033[1m'; C_MAG=$'\033[35m'; C_CYAN=$'\033[96m'; C_RST=$'\033[0m'
else
    C_OK= C_FAIL= C_INFO= C_WARN= C_DIM= C_BOLD= C_MAG= C_CYAN= C_RST=
fi

_log_file() { mkdir -p "$(dirname "$DEPLOY_LOG")" 2>/dev/null || true; echo "[$(date -Iseconds)] $*" >>"$DEPLOY_LOG" 2>/dev/null || true; }
ok()   { echo "${C_OK}  ✅ $*${C_RST}"; _log_file "OK $*"; }
fail() { echo "${C_FAIL}  ❌ $*${C_RST}" >&2; _log_file "FAIL $*"; exit 1; }
info() { echo "${C_INFO}  💡 $*${C_RST}"; _log_file "INFO $*"; }
warn() { echo "${C_WARN}  ⚠️  $*${C_RST}"; _log_file "WARN $*"; }
dry()  { echo "${C_MAG}  👻 $*${C_RST}"; _log_file "DRY $*"; }

profile_emoji() {
    if [ "$UNINSTALL" = true ]; then echo "🗑️"; return; fi
    if [ "$VERIFY_ONLY" = true ]; then echo "🔬"; return; fi
    if [ "$PREFLIGHT_ONLY" = true ]; then echo "🔍"; return; fi
    if [ "$DEPLOY_PROFILE" = "container" ]; then echo "🐳"; return; fi
    if [ "$DEPLOY_PROFILE" = "k3s" ]; then echo "☸️"; return; fi
    [ "$QUICK_MODE" = true ] && echo "⚡" || echo "🏗️"
}

profile_label() {
    if [ "$UNINSTALL" = true ]; then echo "uninstall"; return; fi
    if [ "$VERIFY_ONLY" = true ]; then echo "verify-only"; return; fi
    if [ "$PREFLIGHT_ONLY" = true ]; then echo "preflight"; return; fi
    echo "${DEPLOY_PROFILE}"
}

print_banner() {
    local pe pl target
    pe=$(profile_emoji)
    pl=$(profile_label)
    target="${TARGET_USER}@${TARGET_HOST}"
    [ -z "${TARGET_HOST}" ] && target="(fleet mode)"
    echo ""
    echo "${C_CYAN}${C_BOLD}  ╔══════════════════════════════════════════════════════════╗${C_RST}"
    echo "${C_CYAN}${C_BOLD}  ║${C_RST}  ${pe}  🤖 ${C_BOLD}Zyvor Argus${C_RST} Remote Deploy  ${C_DIM}v${VERSION}${C_RST}          ${C_CYAN}${C_BOLD}║${C_RST}"
    echo "${C_CYAN}${C_BOLD}  ║${C_RST}     🛰️  ${C_BOLD}${target}${C_RST}  ·  profile: ${pe} ${pl}                ${C_CYAN}${C_BOLD}║${C_RST}"
    [ "$DRY_RUN" = true ] && echo "${C_MAG}${C_BOLD}  ║${C_RST}     👻  DRY-RUN — no remote changes                    ${C_MAG}${C_BOLD}║${C_RST}"
    [ -n "${FLEET_FILE}" ] && echo "${C_CYAN}${C_BOLD}  ║${C_RST}     🚢  Fleet: ${FLEET_FILE}                          ${C_CYAN}${C_BOLD}║${C_RST}"
    echo "${C_CYAN}${C_BOLD}  ╚══════════════════════════════════════════════════════════╝${C_RST}"
    echo ""
}

STEP_T0=0
STEP_IDX=0

step_begin() {
    STEP_IDX=$((STEP_IDX + 1))
    STEP_T0=$(date +%s)
    echo ""
    echo "${C_BOLD}${C_CYAN}  ┌─ Step ${STEP_IDX}: $*${C_RST}"
    echo "${C_DIM}  ────────────────────────────────────────────────────────────${C_RST}"
    _log_file "STEP ${STEP_IDX}: $*"
}

step_end() {
    echo "${C_DIM}  └─${C_RST} ${C_OK}✨ finished in $(( $(date +%s) - STEP_T0 ))s${C_RST}"
}

run_step() {
    step_begin "$1"; shift
    if [ "$DRY_RUN" = true ]; then dry "would run: $*"; step_end; return 0; fi
    "$@"; step_end
}

SSH_OPTS="-o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -o ConnectTimeout=15 -o ServerAliveInterval=30"
if [ -z "${TARGET_PASS}" ]; then
    SSH_OPTS+=" -o BatchMode=yes -o PreferredAuthentications=publickey"
fi

_ssh_once() {
    if [ -n "${TARGET_PASS}" ] && command -v sshpass &>/dev/null; then
        export SSHPASS="${TARGET_PASS}"
        sshpass -e ssh ${SSH_OPTS} "${TARGET_USER}@${TARGET_HOST}" "$@"
    else
        ssh ${SSH_OPTS} "${TARGET_USER}@${TARGET_HOST}" "$@"
    fi
}

_ssh() {
    # Buffer stdin (heredoc scripts) so every retry attempt gets the full
    # script — a plain retry would rerun ssh with stdin already consumed,
    # executing an empty script that exits 0 and masks the real failure.
    local _stdin=""
    if [ ! -t 0 ]; then
        _stdin=$(cat)
    fi
    local attempt=1 max="${SSH_RETRIES}"
    while [ "$attempt" -le "$max" ]; do
        if [ -n "${_stdin}" ]; then
            if printf '%s' "${_stdin}" | _ssh_once "$@"; then
                return 0
            fi
        else
            if _ssh_once "$@" </dev/null; then
                return 0
            fi
        fi
        attempt=$((attempt + 1))
        if [ "$attempt" -le "$max" ]; then
            local _d=$(( 2 * (attempt - 1) )); _d=$(( _d < 2 ? 2 : _d > 30 ? 30 : _d ))
            warn "SSH retry ${attempt}/${max}" && sleep "${_d}"
        fi
    done
    return 1
}

_rsync() {
    local opts="-az --delete"
    [ "$VERBOSE" = true ] && opts+=" --progress"
    if [ -n "${TARGET_PASS}" ] && command -v sshpass &>/dev/null; then
        export SSHPASS="${TARGET_PASS}"
        rsync ${opts} -e "sshpass -e ssh ${SSH_OPTS}" "$@"
    else
        rsync ${opts} -e "ssh ${SSH_OPTS}" "$@"
    fi
}

validate() {
    [ -n "${TARGET_HOST}" ] || { usage; exit 1; }
    [ -f "${PROJECT_DIR}/pyproject.toml" ] || fail "Not in zyvor-argus repo: ${PROJECT_DIR}"
    if [ -n "${TARGET_PASS}" ]; then
        warn "Password auth is deprecated. Prefer: ssh-copy-id ${TARGET_USER}@${TARGET_HOST}"
        command -v sshpass &>/dev/null || fail "sshpass required for password auth (dnf/apt install sshpass)"
    fi
}

check_connectivity() {
    info "SSH → ${TARGET_USER}@${TARGET_HOST}  📝 ${DEPLOY_LOG}"
    if [ "$DRY_RUN" = true ]; then
        REMOTE_DIR="${DEPLOY_DIR:-\$HOME/.deployments/zyvor-argus}"
        return 0
    fi
    _ssh "echo ok" &>/dev/null || fail "SSH failed — try: ssh-copy-id ${TARGET_USER}@${TARGET_HOST}"
    ok "SSH connected"
    local remote_home
    remote_home=$(_ssh "echo \$HOME" 2>/dev/null | tr -d '\r')
    remote_home="${remote_home:-/home/${TARGET_USER}}"
    REMOTE_DIR="${DEPLOY_DIR:-${remote_home}/.deployments/zyvor-argus}"
    info "Remote path: ${REMOTE_DIR}"
}

resolve_serve_port() {
    # Explicit --port / ZYVOR_ARGUS_PORT wins; otherwise reuse the port persisted on
    # the remote from a previous deploy; otherwise the fixed default (30080).
    if [ -n "${SERVE_PORT}" ]; then
        [ "$DRY_RUN" = true ] || _ssh "mkdir -p '${REMOTE_DIR}' && echo '${SERVE_PORT}' > '${REMOTE_DIR}/.zyvor-argus-port'"
        info "Serve port: ${SERVE_PORT} (explicit)"
        return 0
    fi
    if [ "$DRY_RUN" = true ]; then
        SERVE_PORT="${DEFAULT_SERVE_PORT}"
        dry "would use fixed default port: ${SERVE_PORT}"
        return 0
    fi
    local existing
    existing=$(_ssh "cat '${REMOTE_DIR}/.zyvor-argus-port' 2>/dev/null" | tr -d '[:space:]' || true)
    if [[ "${existing}" =~ ^[0-9]+$ ]] && [ "${existing}" -ge 1024 ] && [ "${existing}" -le 65535 ]; then
        SERVE_PORT="${existing}"
        info "Serve port: ${SERVE_PORT} (reused from remote)"
        return 0
    fi
    SERVE_PORT="${DEFAULT_SERVE_PORT}"
    _ssh "mkdir -p '${REMOTE_DIR}' && echo '${SERVE_PORT}' > '${REMOTE_DIR}/.zyvor-argus-port'"
    info "Serve port: ${SERVE_PORT} (fixed default, persisted on remote)"
}

resolve_dashboard_auth() {
    # Generate a login once per host (persisted alongside the port file) and
    # write it into the remote .env so every profile picks it up.
    if [ "$NO_AUTH" = true ]; then
        info "Dashboard auth: disabled (--no-auth)"
        return 0
    fi
    if [ "$DRY_RUN" = true ]; then
        DASH_PASS="<generated>"
        dry "would generate dashboard credentials"
        return 0
    fi
    local existing
    existing=$(_ssh "cat '${REMOTE_DIR}/.zyvor-argus-auth' 2>/dev/null" | tr -d '[:space:]' || true)
    if [[ "${existing}" == *:* ]]; then
        DASH_USER="${existing%%:*}"
        DASH_PASS="${existing#*:}"
        info "Dashboard auth: reusing credentials from remote"
    else
        DASH_PASS="${DASH_PASS_DEFAULT}"
        _ssh "mkdir -p '${REMOTE_DIR}' && umask 077 && echo '${DASH_USER}:${DASH_PASS}' > '${REMOTE_DIR}/.zyvor-argus-auth'"
        info "Dashboard auth: default credentials set (persisted on remote)"
    fi
    _ssh env REMOTE_STAGING="${REMOTE_DIR}" DASH_USER="${DASH_USER}" DASH_PASS="${DASH_PASS}" bash <<'REMOTE'
set -e
cd "${REMOTE_STAGING}"
touch .env
grep -v '^DASHBOARD_USER=\|^DASHBOARD_PASSWORD=' .env > .env.tmp || true
{
    cat .env.tmp
    echo "DASHBOARD_USER=${DASH_USER}"
    echo "DASHBOARD_PASSWORD=${DASH_PASS}"
} > .env
rm -f .env.tmp
chmod 600 .env
REMOTE
}

preflight_remote() {
    info "Preflight on ${TARGET_HOST}..."
    if [ "$DRY_RUN" = true ]; then return 0; fi
    _ssh bash <<'REMOTE' || fail "Preflight failed"
set -e
echo "  host: $(hostname -f 2>/dev/null || hostname)"
echo "  os:   $(. /etc/os-release 2>/dev/null && echo "$PRETTY_NAME" || uname -s)"
echo "  arch: $(uname -m)"
echo "  mem:  $(free -h 2>/dev/null | awk '/^Mem:/{print $2}' || echo n/a)"
echo "  disk: $(df -h / 2>/dev/null | awk 'NR==2{print $4 " free on " $1}' || echo n/a)"
AVAIL=$(df -BG / 2>/dev/null | awk 'NR==2{gsub(/G/,"",$4); print $4}' || echo 99)
if [ "${AVAIL}" -lt 3 ] 2>/dev/null; then
    echo "  ⚠️  Less than 3G free on / — Playwright browsers need ~1G"
fi
if [ "$(id -u)" -ne 0 ]; then
    if ! sudo -n true 2>/dev/null; then
        echo "  ❌ Non-root user needs passwordless sudo for package install"
        exit 1
    fi
    echo "  ✅ passwordless sudo"
else
    echo "  ✅ running as root"
fi
command -v python3 >/dev/null && echo "  ✅ python3 $(python3 -V 2>&1 | awk '{print $2}')" || echo "  ⚠️  python3 missing (will install)"
command -v node >/dev/null && echo "  ✅ node $(node -v)" || echo "  ⚠️  node missing (will install)"
command -v rsync >/dev/null && echo "  ✅ rsync" || echo "  ⚠️  rsync missing (will install)"
REMOTE
    ok "Preflight passed"
}

sync_files() {
    if [ "$SKIP_SYNC" = true ]; then
        info "Skipping rsync (--skip-sync)"
        return 0
    fi
    _ssh "command -v rsync >/dev/null || { S=; [ \"\$(id -u)\" -ne 0 ] && S=sudo; \$S apt-get install -y -qq rsync 2>/dev/null || \$S dnf install -y rsync 2>/dev/null || \$S yum install -y rsync; }"
    _ssh "mkdir -p '${REMOTE_DIR}'"
    local excludes=(
        # deploy-state files on the remote — excluded so --delete can't wipe them
        --exclude '.zyvor-argus-port'
        --exclude '.zyvor-argus-auth'
        --exclude '.zyvor-argus-image-tag'
        --exclude '.git'
        --exclude '.venv' --exclude 'venv'
        --exclude 'node_modules'
        --exclude '__pycache__' --exclude '*.pyc' --exclude '*.egg-info'
        --exclude 'rust/target'
        --exclude 'test-results' --exclude 'reports'
        --exclude 'screenshots/current' --exclude 'screenshots/diffs'
        --exclude 'videos' --exclude 'traces'
        --exclude 'tests/fixtures/fetched'
    )
    if [ "$WITH_ENV" != true ]; then
        # excluded (not synced) AND protected from --delete, so a remote-managed
        # .env survives redeploys
        excludes+=(--exclude '.env')
    fi
    _rsync "${excludes[@]}" "${PROJECT_DIR}/" "${TARGET_USER}@${TARGET_HOST}:${REMOTE_DIR}/"
    ok "Source synced to ${REMOTE_DIR}"
    if [ "$WITH_ENV" = true ] && [ -f "${PROJECT_DIR}/.env" ]; then
        warn "Local .env (including secrets) was synced to the remote host"
    fi
}

install_system_deps() {
    _ssh bash <<'REMOTE'
set -euo pipefail
SUDO=""
[ "$(id -u)" -ne 0 ] && SUDO="sudo"

# Prefer apt-get on Debian/Ubuntu even if dnf is installed as an extra package
. /etc/os-release 2>/dev/null || true
_ID="${ID:-}" _ID_LIKE="${ID_LIKE:-}"
if [[ "$_ID" == "debian" || "$_ID" == "ubuntu" || "$_ID_LIKE" == *"debian"* || "$_ID_LIKE" == *"ubuntu"* ]]; then
    PKG=apt-get
    $SUDO apt-get update -qq
elif command -v dnf &>/dev/null; then
    PKG=dnf
elif command -v yum &>/dev/null; then
    PKG=yum
elif command -v apt-get &>/dev/null; then
    PKG=apt-get
    $SUDO apt-get update -qq
else
    echo "ERROR: unsupported package manager"
    exit 1
fi

if [ "$PKG" = "apt-get" ]; then
    $SUDO apt-get install -y -qq python3 python3-venv python3-pip git curl rsync ca-certificates
else
    $SUDO "$PKG" install -y python3 python3-pip git curl rsync ca-certificates
fi

# Node.js 20+ (Playwright requires >= 18; repo targets 20)
NEED_NODE=true
if command -v node &>/dev/null; then
    MAJOR=$(node -v | sed 's/^v//' | cut -d. -f1)
    [ "${MAJOR:-0}" -ge 18 ] && NEED_NODE=false
fi
if [ "$NEED_NODE" = true ]; then
    echo "Installing Node.js 20 via NodeSource..."
    curl -fsSL https://deb.nodesource.com/setup_20.x 2>/dev/null | $SUDO -E bash - 2>/dev/null \
        || curl -fsSL https://rpm.nodesource.com/setup_20.x | $SUDO bash -
    $SUDO "$PKG" install -y nodejs
fi
echo "python3: $(python3 -V 2>&1)"
echo "node:    $(node -v)"
echo "System dependencies installed"
REMOTE
}

install_app_remote() {
    _ssh env REMOTE_STAGING="${REMOTE_DIR}" bash <<'REMOTE'
set -e
SUDO=""
[ "$(id -u)" -ne 0 ] && SUDO="sudo"
cd "${REMOTE_STAGING}"

# Python venv + package
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -e .
echo "  ✅ argus $(.venv/bin/argus --help >/dev/null 2>&1 && echo installed)"

# Node deps + Playwright Chromium (browser deps need root)
npm install --silent --no-fund --no-audit
npx playwright install chromium 2>&1 | tail -2
$SUDO env PATH="$PATH" npx playwright install-deps chromium 2>/dev/null \
    || echo "  ⚠️  playwright install-deps failed (unsupported distro?) — browser may need manual libs"
# cross-browser (flow --browser firefox|webkit) — best-effort, non-fatal
npx playwright install firefox webkit 2>&1 | tail -1 \
    || echo "  ⚠️  firefox/webkit install skipped — cross-browser flow will fall back to chromium"
$SUDO env PATH="$PATH" npx playwright install-deps firefox webkit 2>/dev/null || true

# Default env if none present
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  ⚠️  No .env on remote — created from .env.example (add API keys for LLM features)"
fi

# Global wrapper
$SUDO tee /usr/local/bin/argus >/dev/null <<WRAPPER
#!/usr/bin/env bash
cd "${REMOTE_STAGING}"
exec "${REMOTE_STAGING}/.venv/bin/argus" "\$@"
WRAPPER
$SUDO chmod 755 /usr/local/bin/argus
echo "Installed: /usr/local/bin/argus"
REMOTE
}

install_service() {
    _ssh env REMOTE_STAGING="${REMOTE_DIR}" REMOTE_USER="${TARGET_USER}" SERVE_PORT="${SERVE_PORT}" TLS_MODE="${TLS_MODE:-}" bash <<'REMOTE'
set -e
SUDO=""
[ "$(id -u)" -ne 0 ] && SUDO="sudo"
command -v systemctl >/dev/null || { echo "⚠️  systemd not available — skipping service"; exit 0; }
$SUDO tee /etc/systemd/system/argus.service >/dev/null <<UNIT
[Unit]
Description=Zyvor Argus webhook server + Mission Control dashboard
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${REMOTE_USER}
WorkingDirectory=${REMOTE_STAGING}
ExecStart=${REMOTE_STAGING}/.venv/bin/argus serve --port ${SERVE_PORT} --host 0.0.0.0${TLS_MODE:+ --tls}
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT
$SUDO systemctl daemon-reload
$SUDO systemctl enable argus.service >/dev/null 2>&1 || true
# stop first so the old process releases the port, then start fresh (enable --now
# would NOT restart an already-running service, leaving stale code + a port race)
$SUDO systemctl stop argus.service 2>/dev/null || true
$SUDO pkill -f "argus serve" 2>/dev/null || true
sleep 2
$SUDO systemctl reset-failed argus.service 2>/dev/null || true
$SUDO systemctl start argus.service
for i in $(seq 1 10); do
    sleep 2
    curl -sf "http://127.0.0.1:${SERVE_PORT}/health" >/dev/null && break
done
$SUDO systemctl --no-pager --lines=0 status argus.service | head -3
curl -sf "http://127.0.0.1:${SERVE_PORT}/health" >/dev/null && echo "  ✅ /health responding on :${SERVE_PORT}" || echo "  ⚠️  /health not responding yet"
REMOTE
}

# Shared remote snippet: resolve $CRT to docker or podman (respecting RUNTIME_PREF)
# shellcheck disable=SC2016
RESOLVE_CRT='
CRT=""
if [ -n "${RUNTIME_PREF:-}" ]; then
    command -v "${RUNTIME_PREF}" >/dev/null 2>&1 && CRT="${RUNTIME_PREF}"
elif command -v docker >/dev/null 2>&1; then CRT=docker
elif command -v podman >/dev/null 2>&1; then CRT=podman
fi
'

install_container_runtime() {
    _ssh env RUNTIME_PREF="${RUNTIME_PREF}" bash <<REMOTE
set -euo pipefail
SUDO=""
[ "\$(id -u)" -ne 0 ] && SUDO="sudo"
${RESOLVE_CRT}
if [ -z "\$CRT" ]; then
    . /etc/os-release 2>/dev/null || true
    WANT="\${RUNTIME_PREF:-}"
    if [ -z "\$WANT" ]; then
        case "\${ID:-}\${ID_LIKE:-}" in
            *debian*|*ubuntu*) WANT=docker ;;
            *)                 WANT=podman ;;
        esac
    fi
    echo "Installing \$WANT..."
    if [ "\$WANT" = "docker" ]; then
        curl -fsSL https://get.docker.com | \$SUDO sh
    else
        \$SUDO apt-get install -y -qq podman 2>/dev/null \
            || \$SUDO dnf install -y podman 2>/dev/null \
            || \$SUDO yum install -y podman
    fi
    CRT="\$WANT"
fi
[ "\$CRT" = "docker" ] && \$SUDO systemctl enable --now docker 2>/dev/null || true
if [ "\$CRT" = "podman" ]; then
    # keep --restart policies alive across reboots
    \$SUDO systemctl enable --now podman-restart 2>/dev/null || true
fi
echo "runtime: \$CRT — \$(\$SUDO \$CRT --version)"
REMOTE
}

build_run_container() {
    _ssh env REMOTE_STAGING="${REMOTE_DIR}" SERVE_PORT="${SERVE_PORT}" RUNTIME_PREF="${RUNTIME_PREF}" bash <<REMOTE
set -e
SUDO=""
[ "\$(id -u)" -ne 0 ] && SUDO="sudo"
${RESOLVE_CRT}
[ -n "\$CRT" ] || { echo "❌ no container runtime found"; exit 1; }
cd "\${REMOTE_STAGING}"
[ -f .env ] || cp .env.example .env

echo "Building image zyvor-argus with \$CRT (first build can take a few minutes)..."
\$SUDO \$CRT build -f docker/Dockerfile -t zyvor-argus . 2>&1 | tail -4

\$SUDO \$CRT rm -f argus 2>/dev/null || true
\$SUDO \$CRT run -d --name argus \
    --restart unless-stopped \
    --env-file .env \
    -p "\${SERVE_PORT}:8080" \
    zyvor-argus serve --port 8080 --host 0.0.0.0

sleep 3
\$SUDO \$CRT ps --filter name=argus --format '  {{.Names}}  {{.Status}}  {{.Ports}}'
curl -sf "http://127.0.0.1:\${SERVE_PORT}/health" >/dev/null \
    && echo "  ✅ /health responding on :\${SERVE_PORT} (runtime: \$CRT)" \
    || { echo "  ❌ /health not responding"; \$SUDO \$CRT logs --tail 20 argus; exit 1; }
REMOTE
}

install_k3s_remote() {
    _ssh bash <<'REMOTE'
set -euo pipefail
SUDO=""
[ "$(id -u)" -ne 0 ] && SUDO="sudo"
if ! command -v k3s &>/dev/null; then
    echo "Installing k3s via get.k3s.io..."
    curl -sfL https://get.k3s.io | $SUDO sh -s - --write-kubeconfig-mode 644
fi
$SUDO systemctl enable --now k3s 2>/dev/null || true
for i in $(seq 1 30); do
    $SUDO k3s kubectl get nodes &>/dev/null && break
    sleep 2
done
$SUDO k3s kubectl get nodes
REMOTE
}

build_import_image_k3s() {
    _ssh env REMOTE_STAGING="${REMOTE_DIR}" RUNTIME_PREF="${RUNTIME_PREF}" bash <<REMOTE
set -e
SUDO=""
[ "\$(id -u)" -ne 0 ] && SUDO="sudo"
${RESOLVE_CRT}
[ -n "\$CRT" ] || { echo "❌ no container runtime found (needed to build the image)"; exit 1; }
cd "\${REMOTE_STAGING}"
echo "Building image zyvor-argus with \$CRT..."
\$SUDO \$CRT build -f docker/Dockerfile -t zyvor-argus . 2>&1 | tail -4
# Content-unique tag so re-importing :latest can't dedupe to a stale manifest —
# the pod's imagePullPolicy:Never image always matches the freshly built code.
TAG="zyvor-argus:d\$(date +%Y%m%d%H%M%S)"
DOCKER_TAG="docker.io/library/\${TAG}"
\$SUDO \$CRT tag zyvor-argus:latest "\${DOCKER_TAG}"
echo "Importing \${TAG} into k3s containerd..."
\$SUDO \$CRT save "\${DOCKER_TAG}" | \$SUDO k3s ctr images import -
echo "\${TAG}" > "\${REMOTE_STAGING}/.zyvor-argus-image-tag"
\$SUDO k3s ctr images ls | grep -o "docker.io/library/\${TAG}" | head -1
REMOTE
}

apply_k8s_remote() {
    _ssh env REMOTE_STAGING="${REMOTE_DIR}" SERVE_PORT="${SERVE_PORT}" \
        DASH_USER="${DASH_USER}" DASH_PASS="${DASH_PASS}" bash <<'REMOTE'
set -e
SUDO=""
[ "$(id -u)" -ne 0 ] && SUDO="sudo"
KUBECTL="$SUDO k3s kubectl"
cd "${REMOTE_STAGING}"

IMAGE_TAG=$(cat "${REMOTE_STAGING}/.zyvor-argus-image-tag" 2>/dev/null || echo "zyvor-argus:latest")

# Local image only — pin the content-unique tag + imagePullPolicy: Never so the
# pod always runs the freshly built code and never hits a registry.
WORK=$(mktemp -d)
for f in configmap secret rbac pvc deployment service cronjob; do
    sed -E "s|^([[:space:]]*)image: ghcr.io/zyvorai/zyvor-argus:latest|\1image: ${IMAGE_TAG}\n\1imagePullPolicy: Never|" \
        "kubernetes/${f}.yaml" > "${WORK}/${f}.yaml"
done
$KUBECTL apply -f "${WORK}/configmap.yaml" -f "${WORK}/secret.yaml" -f "${WORK}/rbac.yaml" \
    -f "${WORK}/pvc.yaml" -f "${WORK}/deployment.yaml" -f "${WORK}/service.yaml" -f "${WORK}/cronjob.yaml"
rm -rf "${WORK}"

# Dashboard login — patch credentials into the secret before the rollout below
if [ -n "${DASH_PASS:-}" ] && [ "${DASH_PASS}" != "<generated>" ]; then
    $KUBECTL patch secret argus-secrets --type merge -p \
        "{\"stringData\":{\"DASHBOARD_USER\":\"${DASH_USER}\",\"DASHBOARD_PASSWORD\":\"${DASH_PASS}\"}}"
    echo "  Dashboard credentials injected into secret"
fi

# Expose the webhook + dashboard on the deploy port (NodePort range 30000-32767)
if [ "${SERVE_PORT}" -ge 30000 ] && [ "${SERVE_PORT}" -le 32767 ]; then
    $KUBECTL patch svc argus-webhook -p \
        "{\"spec\":{\"type\":\"NodePort\",\"ports\":[{\"port\":80,\"targetPort\":8080,\"nodePort\":${SERVE_PORT}}]}}"
    echo "  Service exposed: NodePort ${SERVE_PORT}"
else
    echo "  ⚠️  Port ${SERVE_PORT} outside NodePort range — Service left as ClusterIP"
fi

# The unique image tag already changes the pod spec, so apply triggers a fresh
# rollout; restart as well to be safe on unchanged-tag redeploys.
$KUBECTL rollout restart deployment/argus-webhook
$KUBECTL rollout status deployment/argus-webhook --timeout=180s
$KUBECTL get pods -l app=argus -o wide
curl -sf "http://127.0.0.1:${SERVE_PORT}/health" >/dev/null \
    && echo "  ✅ /health responding on NodePort :${SERVE_PORT}" \
    || { echo "  ❌ /health not responding"; $KUBECTL logs -l app=argus --tail=20; exit 1; }
REMOTE
}

verify_remote() {
    info "Verifying on ${TARGET_HOST}..."
    if [ "$DRY_RUN" = true ]; then
        dry "would run: argus --help + pipeline import check"
        return 0
    fi
    # Single SSH attempt — do not retry when verification exits non-zero
    if _ssh_once env REMOTE_STAGING="${REMOTE_DIR}" bash <<'REMOTE'
set -e
cd "${REMOTE_STAGING}"
echo "  argus: $(command -v argus || echo missing)"
argus --help >/dev/null && echo "  ✅ CLI responds"
.venv/bin/python -c "from orchestrator.graph import get_compiled_graph; get_compiled_graph()" \
    && echo "  ✅ pipeline graph compiles"
echo "  node $(node -v) · playwright $(npx playwright --version | awk '{print $2}')"
.venv/bin/python -c "
from playwright.__main__ import main" 2>/dev/null || true
ls "$HOME/.cache/ms-playwright" 2>/dev/null | grep -qi chromium && echo "  ✅ Chromium browser present" || echo "  ⚠️  Chromium not found in ~/.cache/ms-playwright"
REMOTE
    then
        ok "Verification passed"
    else
        warn "Verification reported failures (agent files are on the host; see above)"
        return 0
    fi
}

run_smoke_remote() {
    info "Running smoke tests on ${TARGET_HOST} (argus test exec)..."
    if [ "$DRY_RUN" = true ]; then dry "would run: argus test exec"; return 0; fi
    local cmd
    case "${DEPLOY_PROFILE}" in
        container)
            cmd="S=; [ \"\$(id -u)\" -ne 0 ] && S=sudo; CRT=docker; command -v docker >/dev/null || CRT=podman; \$S \$CRT exec argus argus test exec"
            ;;
        k3s)
            cmd="S=; [ \"\$(id -u)\" -ne 0 ] && S=sudo; \$S k3s kubectl exec deploy/argus-webhook -- argus test exec"
            ;;
        *)
            cmd="cd '${REMOTE_DIR}' && argus test exec"
            ;;
    esac
    if _ssh_once "${cmd}"; then
        ok "Smoke tests passed"
    else
        warn "Smoke tests reported failures (see output above)"
        return 0
    fi
}

do_uninstall() {
    _ssh env REMOTE_STAGING="${REMOTE_DIR}" bash <<'REMOTE'
set -e
SUDO=""
[ "$(id -u)" -ne 0 ] && SUDO="sudo"
# systemd service
if command -v systemctl >/dev/null && [ -f /etc/systemd/system/argus.service ]; then
    $SUDO systemctl disable --now argus.service 2>/dev/null || true
    $SUDO rm -f /etc/systemd/system/argus.service
    $SUDO systemctl daemon-reload
    echo "  removed systemd service"
fi
# container (docker or podman)
for CRT in docker podman; do
    if command -v "$CRT" >/dev/null 2>&1; then
        $SUDO "$CRT" rm -f argus 2>/dev/null && echo "  removed $CRT container" || true
        $SUDO "$CRT" rmi -f zyvor-argus 2>/dev/null || true
    fi
done
# k3s resources (cluster itself is left alone)
if command -v k3s >/dev/null 2>&1; then
    $SUDO k3s kubectl delete deployment,service,cronjob,configmap,secret,role,rolebinding,serviceaccount \
        -l app=argus --ignore-not-found 2>/dev/null || true
    $SUDO k3s ctr images rm docker.io/library/zyvor-argus:latest 2>/dev/null || true
    echo "  removed k8s resources (k3s itself left installed)"
fi
$SUDO rm -f /usr/local/bin/argus
rm -rf "${REMOTE_STAGING}"
echo "argus removed"
REMOTE
    ok "Uninstalled on ${TARGET_HOST}"
}

deploy_profile_full() {
    run_step "Sync sources" sync_files
    run_step "System dependencies" install_system_deps
    run_step "Install app (venv + npm + Playwright)" install_app_remote
    [ "$INSTALL_SERVICE" = true ] && run_step "Systemd service" install_service
    return 0
}

deploy_profile_quick() {
    run_step "Sync sources" sync_files
    run_step "Install app (venv + npm + Playwright)" install_app_remote
    [ "$INSTALL_SERVICE" = true ] && run_step "Systemd service" install_service
    return 0
}

deploy_profile_container() {
    run_step "Sync sources" sync_files
    run_step "Container runtime (docker/podman)" install_container_runtime
    run_step "Build image + run container" build_run_container
}

deploy_profile_k3s() {
    run_step "Sync sources" sync_files
    run_step "Container runtime (docker/podman)" install_container_runtime
    run_step "k3s cluster" install_k3s_remote
    run_step "Build image + import into k3s" build_import_image_k3s
    run_step "Deploy K8s resources (pods, RBAC, cronjob)" apply_k8s_remote
}

print_deployment_summary() {
    local pe pl
    pe=$(profile_emoji)
    pl=$(profile_label)
    echo ""
    echo "${C_OK}${C_BOLD}  ╔══════════════════════════════════════════════════════════╗${C_RST}"
    echo "${C_OK}${C_BOLD}  ║${C_RST}  🎉  Deploy complete — ${C_BOLD}${TARGET_USER}@${TARGET_HOST}${C_RST}  ·  ${pe} ${pl}      ${C_OK}${C_BOLD}║${C_RST}"
    echo "${C_OK}${C_BOLD}  ╚══════════════════════════════════════════════════════════╝${C_RST}"
    echo ""
    echo "  📝  Log         ${DEPLOY_LOG}"
    echo "  📁  Remote      ${REMOTE_DIR}"
    [ -n "${SERVE_PORT}" ] && \
    echo "  📌  NodePort    ${SERVE_PORT}  ${C_DIM}(fixed — persisted; override with --port)${C_RST}"
    if [ "$NO_AUTH" != true ] && [ -n "${DASH_PASS}" ]; then
        echo "  🔐  Login       ${C_BOLD}${DASH_USER}${C_RST} / ${C_BOLD}${DASH_PASS}${C_RST}  ${C_DIM}(persisted in ${REMOTE_DIR}/.zyvor-argus-auth)${C_RST}"
    fi
    echo ""
    case "${DEPLOY_PROFILE}" in
        container)
            echo "  📺  ${C_BOLD}http://${TARGET_HOST}:${SERVE_PORT}/dashboard${C_RST}   Mission Control"
            echo "  ❤️   http://${TARGET_HOST}:${SERVE_PORT}/health"
            echo "  🪝  http://${TARGET_HOST}:${SERVE_PORT}/webhook/github"
            echo "  🐳  ssh ${TARGET_USER}@${TARGET_HOST} 'sudo docker logs -f argus'  ${C_DIM}(or podman)${C_RST}"
            ;;
        k3s)
            echo "  📺  ${C_BOLD}http://${TARGET_HOST}:${SERVE_PORT}/dashboard${C_RST}   Mission Control (live pods!)"
            echo "  ❤️   http://${TARGET_HOST}:${SERVE_PORT}/health"
            echo "  🪝  http://${TARGET_HOST}:${SERVE_PORT}/webhook/github"
            echo "  ☸️   ssh ${TARGET_USER}@${TARGET_HOST} 'sudo k3s kubectl get pods -o wide'"
            ;;
        *)
            echo "  🔗  ssh ${TARGET_USER}@${TARGET_HOST}"
            echo "  🧪  argus test exec"
            echo "  🚀  argus test run --source local"
            if [ "$INSTALL_SERVICE" = true ]; then
                echo "  📺  ${C_BOLD}http://${TARGET_HOST}:${SERVE_PORT}/dashboard${C_RST}   Mission Control"
                echo "  🔧  sudo systemctl status argus"
            else
                echo "  📺  argus serve --port ${SERVE_PORT}   → http://${TARGET_HOST}:${SERVE_PORT}/dashboard"
            fi
            ;;
    esac
    echo ""
}

deploy_fleet() {
    local hosts_file="$1"
    [ -f "$hosts_file" ] || fail "Fleet file not found: $hosts_file"
    chmod 600 "$hosts_file" 2>/dev/null || true
    local count=0
    while IFS=' ' read -r host user pass opts; do
        [ -z "$host" ] && continue
        [[ "$host" =~ ^# ]] && continue
        count=$((count + 1))
        TARGET_HOST="$host"
        TARGET_USER="${user:-root}"
        TARGET_PASS="${pass:-}"
        if [[ "$host" == *"@"* ]]; then
            TARGET_USER="${host%%@*}"
            TARGET_HOST="${host#*@}"
        fi
        STEP_IDX=0
        print_banner
        check_connectivity
        preflight_remote
        resolve_serve_port
        resolve_dashboard_auth
        if [[ "${opts:-}" == *"--uninstall"* ]]; then
            run_step "Uninstall" do_uninstall
        elif [[ "${opts:-}" == *"--k3s"* ]]; then
            DEPLOY_PROFILE="k3s"
            deploy_profile_k3s
        elif [[ "${opts:-}" == *"--container"* ]]; then
            DEPLOY_PROFILE="container"
            deploy_profile_container
        elif [[ "${opts:-}" == *"--quick"* ]]; then
            QUICK_MODE=true
            deploy_profile_quick
        else
            deploy_profile_full
        fi
        if [ "$SKIP_VERIFY" != true ] && [[ "${DEPLOY_PROFILE}" != "container" && "${DEPLOY_PROFILE}" != "k3s" ]]; then
            verify_remote
        fi
        print_deployment_summary
    done < "$hosts_file"
    ok "Fleet complete — ${count} host(s)"
}

main() {
    print_banner
    if [ -n "${FLEET_FILE}" ]; then
        validate
        deploy_fleet "${FLEET_FILE}"
        exit 0
    fi
    validate
    check_connectivity
    preflight_remote

    if [ "$PREFLIGHT_ONLY" = true ]; then
        ok "Preflight-only complete"
        exit 0
    fi

    if [ "$UNINSTALL" = true ]; then
        run_step "Uninstall argus" do_uninstall
        exit 0
    fi

    resolve_serve_port
    resolve_dashboard_auth

    if [ "$VERIFY_ONLY" = true ]; then
        [ "$SKIP_VERIFY" != true ] && run_step "Verify" verify_remote
        print_deployment_summary
        exit 0
    fi

    case "${DEPLOY_PROFILE}" in
        quick)     deploy_profile_quick ;;
        container) deploy_profile_container ;;
        k3s)       deploy_profile_k3s ;;
        *)         deploy_profile_full ;;
    esac

    # container/k3s profiles health-check inline; bare-host profiles get the venv verify
    if [ "$SKIP_VERIFY" != true ] && [[ "${DEPLOY_PROFILE}" != "container" && "${DEPLOY_PROFILE}" != "k3s" ]]; then
        run_step "Verify" verify_remote
    fi
    [ "$RUN_SMOKE" = true ] && run_step "Smoke tests" run_smoke_remote
    print_deployment_summary
}

main "$@"
