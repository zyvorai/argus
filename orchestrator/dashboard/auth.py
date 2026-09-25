# Copyright 2026 Zyvor AI Labs · https://zyvor.dev
# SPDX-License-Identifier: LicenseRef-Zyvor-Production-1.0
"""Session auth for Mission Control — active when DASHBOARD_PASSWORD is set.

Signed-cookie sessions with no extra dependencies:
    cookie = "<expiry>:<hmac_sha256(secret, user + expiry)>"
The secret is DASHBOARD_SECRET, or derived from the credentials so sessions
survive pod restarts without extra configuration.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import threading
import time
from collections import defaultdict, deque
from typing import Any

COOKIE_NAME = "zyvor_qa_session"
CSRF_COOKIE_NAME = "zyvor_qa_csrf"
SESSION_HOURS = 12
REMEMBER_DAYS = 30

# ── login rate limiting (per client IP, sliding window) ──
RL_WINDOW_S = 300          # 5-minute window
RL_MAX_FAILURES = 8        # failures allowed in the window before lockout
RL_LOCKOUT_S = 300         # lockout duration once tripped
_rl_lock = threading.Lock()
_rl_failures: dict[str, deque[float]] = defaultdict(deque)
_rl_locked_until: dict[str, float] = {}
_rl_last_prune = 0.0


def _rl_prune(now: float) -> None:
    """Drop stale IP entries so the maps don't grow unbounded (call under _rl_lock)."""
    global _rl_last_prune
    if now - _rl_last_prune < RL_WINDOW_S:
        return
    _rl_last_prune = now
    for ip in list(_rl_failures):
        dq = _rl_failures[ip]
        while dq and dq[0] < now - RL_WINDOW_S:
            dq.popleft()
        if not dq:
            del _rl_failures[ip]
    for ip in list(_rl_locked_until):
        if _rl_locked_until[ip] <= now:
            del _rl_locked_until[ip]


def rate_limited(ip: str) -> int:
    """Return remaining lockout seconds for this IP (0 = allowed to attempt)."""
    now = time.time()
    with _rl_lock:
        until = _rl_locked_until.get(ip, 0)
        if until > now:
            return int(until - now) + 1
        if until:
            _rl_locked_until.pop(ip, None)
        return 0


def record_failure(ip: str) -> None:
    """Record a failed login; trip a lockout once too many failures accrue."""
    now = time.time()
    with _rl_lock:
        _rl_prune(now)
        dq = _rl_failures[ip]
        dq.append(now)
        while dq and dq[0] < now - RL_WINDOW_S:
            dq.popleft()
        if len(dq) >= RL_MAX_FAILURES:
            _rl_locked_until[ip] = now + RL_LOCKOUT_S
            dq.clear()


def record_success(ip: str) -> None:
    """Clear failure state for an IP after a successful login."""
    with _rl_lock:
        _rl_failures.pop(ip, None)
        _rl_locked_until.pop(ip, None)

OPEN_PATHS = {"/health", "/login", "/api/login", "/favicon.ico"}
PROTECTED_PREFIXES = ("/dashboard", "/api/dashboard", "/reports", "/screenshots")


def enabled() -> bool:
    return bool(os.environ.get("DASHBOARD_PASSWORD"))


def username() -> str:
    return os.environ.get("DASHBOARD_USER", "admin")


def _secret() -> bytes:
    explicit = os.environ.get("DASHBOARD_SECRET")
    if explicit:
        return explicit.encode()
    # Derive a signing key when no explicit secret is set. pbkdf2 (not a
    # single SHA-256) so the password isn't used as a fast hash input.
    seed = f"{username()}:{os.environ.get('DASHBOARD_PASSWORD', '')}".encode()
    return hashlib.pbkdf2_hmac("sha256", seed, b"argus-dashboard-v1", 120_000)


def verify_credentials(user: str, password: str) -> bool:
    ok_user = hmac.compare_digest((user or "").encode(), username().encode())
    ok_pass = hmac.compare_digest(
        (password or "").encode(),
        os.environ.get("DASHBOARD_PASSWORD", "").encode(),
    )
    if not (ok_user and ok_pass):
        time.sleep(1.0)  # cheap brute-force damping
        return False
    return True


def _sign(expiry: int) -> str:
    return hmac.new(_secret(), f"{username()}:{expiry}".encode(), hashlib.sha256).hexdigest()


def issue_token(remember: bool = False) -> tuple[str, int]:
    """Return (cookie value, max_age seconds)."""
    max_age = REMEMBER_DAYS * 86400 if remember else SESSION_HOURS * 3600
    expiry = int(time.time()) + max_age
    return f"{expiry}:{_sign(expiry)}", max_age


def validate_token(token: str | None) -> bool:
    if not token or ":" not in token:
        return False
    expiry_raw, sig = token.split(":", 1)
    try:
        expiry = int(expiry_raw)
    except ValueError:
        return False
    if expiry < time.time():
        return False
    return hmac.compare_digest(sig, _sign(expiry))


def is_authenticated(request: Any) -> bool:
    if not enabled():
        return True
    return validate_token(request.cookies.get(COOKIE_NAME))


def csrf_token_for(session_token: str) -> str:
    """Derive the (JS-readable) CSRF cookie value from an already-signed
    session token — nothing new to issue or store server-side."""
    return hashlib.sha256(f"{session_token}:csrf".encode()).hexdigest()


def csrf_valid(request: Any) -> bool:
    """Double-submit check: the X-CSRF-Token header must match the value
    derived from the caller's own (valid) session cookie. Cross-site
    attackers can get the session cookie auto-attached (mitigated by
    SameSite=Lax, but this is defense in depth) yet cannot read it to
    reproduce this header, since document.cookie is scoped per-origin."""
    session_token = request.cookies.get(COOKIE_NAME)
    if not session_token or not validate_token(session_token):
        return False
    expected = csrf_token_for(session_token)
    provided = request.headers.get("x-csrf-token", "")
    return bool(provided) and hmac.compare_digest(expected, provided)


def requires_auth(path: str) -> bool:
    if not enabled():
        return False
    if path.rstrip("/") in OPEN_PATHS or path in {"/webhook/github", "/webhook/slack/command"}:
        return False
    return any(path == p or path.startswith(p + "/") or path.startswith(p + "?") or path.startswith(p)
               for p in PROTECTED_PREFIXES)
