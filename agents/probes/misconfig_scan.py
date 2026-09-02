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

"""Deeper misconfig/recon checks bundled into one scan: tech + version
fingerprinting, wordlist-driven path discovery, security-header *value*
grading (not just presence), and basic DNS hygiene (SPF/DMARC/CAA).

Detection-only — no credential guessing, no login attempts, no exploitation.
Gated behind the security-engagement authorization primitive
(`orchestrator/security/engagement_policy.py`) at the `active_recon` tier;
see `orchestrator/dashboard/jobs.py`'s `_job_misconfig_scan`.
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import urlparse

Log = Optional[Callable[[str], None]]

_DATA_DIR = Path(__file__).resolve().parent / "data"
_DEFAULT_WORDLIST_PATH = _DATA_DIR / "misconfig_paths.txt"

_TECH_SIGNATURES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("WordPress", re.compile(r"wp-content|wp-includes", re.IGNORECASE)),
    ("Drupal", re.compile(r"drupal", re.IGNORECASE)),
    ("Joomla", re.compile(r"joomla", re.IGNORECASE)),
    ("jQuery", re.compile(r"jquery", re.IGNORECASE)),
    ("Next.js", re.compile(r"__NEXT_DATA__", re.IGNORECASE)),
    ("React", re.compile(r"react-dom", re.IGNORECASE)),
)

_VERSIONED_HEADER_RE = re.compile(r"([A-Za-z][\w.-]*)/(\d+(?:\.\d+){1,3})")
_GENERATOR_RE = re.compile(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)', re.IGNORECASE)
_GENERATOR_VERSION_RE = re.compile(r"([A-Za-z][\w.\s]*?)\s+v?(\d+(?:\.\d+){1,3})")
_JQUERY_VERSION_RE = re.compile(r"jquery[.-](\d+\.\d+\.\d+)", re.IGNORECASE)

_WEAK_CSP_TOKENS = ("unsafe-inline", "unsafe-eval")
_HSTS_MIN_MAX_AGE_S = 15_768_000  # ~6 months


def _client(insecure: bool = False):
    import httpx

    return httpx.Client(timeout=15, verify=not insecure, follow_redirects=True)


def _origin(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


def load_wordlist(path: Path | None = None) -> list[str]:
    target = path or _DEFAULT_WORDLIST_PATH
    if not target.is_file():
        return []
    return [
        line.strip()
        for line in target.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def extract_versions(headers: dict[str, str], body: str) -> list[dict[str, str]]:
    """Best-effort product/version extraction from response headers, the
    generator meta tag, and a few common static-asset version strings —
    the source data `cve_lookup.py` matches against known advisories."""
    lowered = {k.lower(): v for k, v in headers.items()}
    found: list[dict[str, str]] = []
    for header_name in ("server", "x-powered-by"):
        for match in _VERSIONED_HEADER_RE.finditer(lowered.get(header_name, "")):
            found.append({"product": match.group(1), "version": match.group(2), "source": f"header:{header_name}"})
    generator = _GENERATOR_RE.search(body)
    if generator:
        generator_match = _GENERATOR_VERSION_RE.search(generator.group(1))
        if generator_match:
            found.append({
                "product": generator_match.group(1).strip(),
                "version": generator_match.group(2),
                "source": "meta:generator",
            })
    jquery = _JQUERY_VERSION_RE.search(body)
    if jquery:
        found.append({"product": "jQuery", "version": jquery.group(1), "source": "asset:jquery"})

    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, str]] = []
    for item in found:
        key = (item["product"].lower(), item["version"])
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def fingerprint_tech(url: str, *, insecure: bool = False) -> dict[str, Any]:
    with _client(insecure=insecure) as c:
        r = c.get(url)
    body = r.text[:200_000]
    server = r.headers.get("server", "")
    signatures = [name for name, pattern in _TECH_SIGNATURES if pattern.search(body) or pattern.search(server)]
    return {
        "status_code": r.status_code,
        "server": server,
        "signatures": signatures,
        "versions": extract_versions(dict(r.headers), body),
    }


def discover_paths(
    url: str,
    *,
    wordlist: list[str] | None = None,
    max_paths: int = 60,
    rate_limit_rps: float = 5.0,
    insecure: bool = False,
    log: Log = None,
) -> dict[str, Any]:
    """Bounded, rate-limited GET sweep over a wordlist — reuses the SPA-aware
    hit-detection from `agents.probes.http_probes.security_paths` (a status-200
    catch-all page isn't a real exposed file) but driven by a much larger word
    list. Not a dirb/gobuster reimplementation: capped path count, throttled."""
    origin = _origin(url)
    paths = (wordlist if wordlist is not None else load_wordlist())[: max(0, min(max_paths, 300))]
    delay = 1.0 / max(rate_limit_rps, 0.1)
    rows: list[list[str]] = []
    exposed: list[str] = []
    with _client(insecure=insecure) as c:
        for p in paths:
            try:
                r = c.get(origin + p, follow_redirects=False)
                ctype = r.headers.get("content-type", "").lower()
                is_html = "text/html" in ctype
                hit = r.status_code == 200 and len(r.content) > 0 and not is_html
                if hit:
                    exposed.append(p)
                    rows.append([p, str(r.status_code), "EXPOSED"])
                    if log:
                        log(f"misconfig_scan: {r.status_code} {p} EXPOSED")
            except Exception:
                pass
            time.sleep(delay)
    return {"checked": len(paths), "exposed": exposed, "rows": rows}


def grade_security_headers(headers: dict[str, str]) -> dict[str, Any]:
    """Presence *and* value grading — extends the presence-only check in
    `playwright/scripts/audit-site.mjs`'s `checkHeaders()`."""
    lowered = {k.lower(): v for k, v in headers.items()}
    issues: list[str] = []

    csp = lowered.get("content-security-policy", "")
    if not csp:
        issues.append("missing Content-Security-Policy")
    else:
        if any(token in csp for token in _WEAK_CSP_TOKENS):
            issues.append("CSP allows 'unsafe-inline'/'unsafe-eval'")
        if "default-src" not in csp:
            issues.append("CSP has no default-src directive")

    hsts = lowered.get("strict-transport-security", "")
    if not hsts:
        issues.append("missing Strict-Transport-Security")
    else:
        match = re.search(r"max-age=(\d+)", hsts)
        max_age = int(match.group(1)) if match else 0
        if max_age < _HSTS_MIN_MAX_AGE_S:
            issues.append(f"HSTS max-age too short ({max_age}s, want ≥{_HSTS_MIN_MAX_AGE_S})")

    for header, label in (
        ("x-content-type-options", "X-Content-Type-Options"),
        ("x-frame-options", "X-Frame-Options"),
        ("referrer-policy", "Referrer-Policy"),
    ):
        if not lowered.get(header):
            issues.append(f"missing {label}")

    status = "fail" if len(issues) >= 4 else "warn" if issues else "ok"
    return {"issues": issues, "status": status}


_CONSENT_MARKERS = (
    "onetrust", "cookiebot", "cookie-consent", "cookieconsent", "cookie-banner",
    "cookie_banner", "gdpr-consent", "trustarc", "quantcast", "osano", "cookieyes",
    "iubenda", "cookie-notice", "cc-window",  # cookieconsent.js's default class
)

_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CC_CANDIDATE_RE = re.compile(r"\b(?:\d[ -]?){13,19}\b")


def check_security_txt(url: str, *, insecure: bool = False) -> dict[str, Any]:
    """RFC 9116 security.txt presence + required-field check:
    `/.well-known/security.txt` (preferred), falling back to the legacy
    `/security.txt`. Degrades gracefully (`checked: False`) if unreachable,
    same posture as `check_dns_hygiene`."""
    origin = _origin(url)
    try:
        with _client(insecure=insecure) as c:
            resp = c.get(f"{origin}/.well-known/security.txt")
            if resp.status_code != 200 or not resp.text.strip():
                resp = c.get(f"{origin}/security.txt")
    except Exception:
        return {"checked": False, "found": False, "issues": []}

    if resp.status_code != 200 or not resp.text.strip():
        return {
            "checked": True, "found": False,
            "issues": ["no security.txt found at /.well-known/security.txt or /security.txt"],
        }

    body = resp.text
    issues = []
    if "Contact:" not in body:
        issues.append("security.txt missing required Contact field")
    if "Expires:" not in body:
        issues.append("security.txt missing required Expires field")
    return {"checked": True, "found": True, "issues": issues}


def check_consent_signals(body: str) -> dict[str, Any]:
    """Heuristic-only: looks for common consent-management-platform script/DOM
    markers in the page's initial HTML. Not a legal/compliance determination —
    a false negative doesn't mean the site lacks a real consent mechanism (it
    may load one after JS execution this black-box check doesn't wait for),
    and a false positive doesn't mean the mechanism is correctly configured."""
    lowered = body.lower()
    found = [m for m in _CONSENT_MARKERS if m in lowered]
    return {"checked": True, "found": bool(found), "markers": found}


def _luhn_valid(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def scan_pii_patterns(body: str) -> dict[str, Any]:
    """Regex sweep for SSN-shaped and Luhn-valid credit-card-shaped strings
    appearing verbatim in a response body. Deliberately does NOT scan for bare
    email addresses — a support/contact address in a footer is normal on
    almost every real site and would make this check pure noise; SSN-shaped
    and Luhn-valid card-shaped values are rare enough in legitimate content
    to be a genuinely low-noise signal."""
    issues: list[str] = []
    if _SSN_RE.search(body):
        issues.append("SSN-shaped value (###-##-####) found in response body")
    for match in _CC_CANDIDATE_RE.finditer(body):
        digits = re.sub(r"[ -]", "", match.group(0))
        if 13 <= len(digits) <= 19 and _luhn_valid(digits):
            issues.append("Luhn-valid credit-card-shaped value found in response body")
            break
    return {"checked": True, "issues": issues}


def check_dns_hygiene(host: str, *, insecure: bool = False) -> dict[str, Any]:
    """SPF/DMARC/CAA presence via Google's DNS-over-HTTPS JSON API — reuses
    `httpx` (already a dependency) instead of adding a DNS library. Degrades
    gracefully (no findings, `checked: False`) if that endpoint is unreachable,
    e.g. in an offline/air-gapped run."""
    try:
        with _client(insecure=insecure) as c:
            spf = c.get("https://dns.google/resolve", params={"name": host, "type": "TXT"}).json()
            dmarc = c.get("https://dns.google/resolve", params={"name": f"_dmarc.{host}", "type": "TXT"}).json()
            caa = c.get("https://dns.google/resolve", params={"name": host, "type": "CAA"}).json()
    except Exception:
        return {"checked": False, "issues": []}

    def _has_txt(payload: dict[str, Any], needle: str) -> bool:
        return any(needle in str(a.get("data", "")) for a in payload.get("Answer", []) or [])

    spf_found = _has_txt(spf, "v=spf1")
    dmarc_found = _has_txt(dmarc, "v=DMARC1")
    caa_found = bool(caa.get("Answer"))

    issues = []
    if not spf_found:
        issues.append("no SPF TXT record")
    if not dmarc_found:
        issues.append("no DMARC TXT record (_dmarc subdomain)")
    if not caa_found:
        issues.append("no CAA record")
    return {"checked": True, "spf": spf_found, "dmarc": dmarc_found, "caa": caa_found, "issues": issues}


def run_misconfig_scan(
    url: str,
    *,
    max_paths: int = 60,
    rate_limit_rps: float = 5.0,
    insecure: bool = False,
    log: Log = None,
) -> dict[str, Any]:
    if log:
        log(f"misconfig_scan: fingerprinting {url}")
    tech = fingerprint_tech(url, insecure=insecure)

    with _client(insecure=insecure) as c:
        header_response = c.get(url)
    headers_grade = grade_security_headers(dict(header_response.headers))

    if log:
        log(f"misconfig_scan: sweeping up to {max_paths} common paths")
    paths = discover_paths(url, max_paths=max_paths, rate_limit_rps=rate_limit_rps, insecure=insecure, log=log)

    host = urlparse(url).hostname or ""
    dns_hygiene = check_dns_hygiene(host, insecure=insecure) if host else {"checked": False, "issues": []}

    if log:
        log("misconfig_scan: checking compliance signals (security.txt, consent, PII patterns)")
    compliance = {
        "security_txt": check_security_txt(url, insecure=insecure),
        "consent": check_consent_signals(header_response.text),
        "pii": scan_pii_patterns(header_response.text),
    }

    return {
        "url": url, "tech": tech, "headers": headers_grade, "paths": paths, "dns": dns_hygiene,
        "compliance": compliance,
    }
