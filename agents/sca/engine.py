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

"""Dependency/license scanning of the TARGET app -- two independent modes.

Black-box mode: reuses `agents.probes.misconfig_scan.fingerprint_tech()`'s
client-side library/version fingerprinting, cross-referenced against a small
bundled license map (`agents/probes/data/license_map.json`). Explicitly
narrow -- dozens of well-known libraries, not a real SBOM. Argus has no
access to the target's actual dependency manifest in the general black-box
case.

Local-checkout mode: subprocess-wraps `pip-audit`/`npm audit` against an
operator-local checkout path (never fetched over the network -- no "target"
is being attacked, so this mode needs no SSRF/engagement gating, unlike
black-box mode). Tools are optional (`shutil.which`-detected): absence
degrades to `skipped: True` with a reason, never a fabricated result and
never a hard error -- same "refuse rather than silently guess" posture this
codebase applies elsewhere, aimed at not overclaiming what wasn't actually
checked.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

_PERMISSIVE_LICENSES = {
    "MIT", "ISC", "BSD-2-CLAUSE", "BSD-3-CLAUSE", "0BSD", "APACHE-2.0", "UNLICENSE", "CC0-1.0",
}


def _license_map() -> dict[str, str]:
    from agents.probes import misconfig_scan

    path = Path(misconfig_scan.__file__).resolve().parent / "data" / "license_map.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {k: v for k, v in data.items() if not k.startswith("_")}


def scan_blackbox(url: str, *, insecure: bool = False) -> dict[str, Any]:
    from agents.probes.misconfig_scan import fingerprint_tech

    tech = fingerprint_tech(url, insecure=insecure)
    license_map = _license_map()
    libraries = []
    for item in tech.get("versions", []):
        product = item["product"]
        license_id = license_map.get(product.lower())
        if license_id is None:
            risk = "unknown"
        elif license_id.split()[0].rstrip(",").upper() not in _PERMISSIVE_LICENSES:
            risk = "copyleft-or-restricted"
        else:
            risk = None
        libraries.append({"product": product, "version": item.get("version", ""), "license": license_id, "risk": risk})
    return {"url": url, "libraries": libraries}


def _detect_ecosystem(checkout_path: Path) -> str | None:
    if (checkout_path / "requirements.txt").exists() or (checkout_path / "pyproject.toml").exists():
        return "python"
    if (checkout_path / "package.json").exists():
        return "npm"
    return None


def scan_local_checkout(checkout_path: str) -> dict[str, Any]:
    root = Path(checkout_path)
    if not root.is_dir():
        return {"checkout_path": checkout_path, "skipped": True, "reason": "checkout_path is not a directory"}

    ecosystem = _detect_ecosystem(root)
    if ecosystem is None:
        return {"checkout_path": checkout_path, "skipped": True,
                 "reason": "no requirements.txt/pyproject.toml or package.json found"}

    if ecosystem == "python":
        tool = shutil.which("pip-audit")
        if not tool:
            return {"checkout_path": checkout_path, "ecosystem": "python", "skipped": True,
                     "reason": "pip-audit not found on PATH -- install the 'sca' extra"}
        # Without -r/a project path, pip-audit audits the *running* Python
        # environment, not the checkout -- a real bug caught in live
        # verification. requirements.txt gets pinned via -r (deterministic,
        # doesn't need dependency resolution); pyproject.toml-only projects
        # go through pip-audit's own project-path resolution instead.
        if (root / "requirements.txt").exists():
            cmd = [tool, "--format", "json", "-r", "requirements.txt"]
        else:
            cmd = [tool, "--format", "json", str(root)]
    else:
        tool = shutil.which("npm")
        if not tool:
            return {"checkout_path": checkout_path, "ecosystem": "npm", "skipped": True,
                     "reason": "npm not found on PATH"}
        cmd = [tool, "audit", "--json"]

    try:
        proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"checkout_path": checkout_path, "ecosystem": ecosystem, "skipped": True,
                 "reason": f"{cmd[0]} failed to run: {exc}"}

    try:
        raw = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return {"checkout_path": checkout_path, "ecosystem": ecosystem, "skipped": True,
                 "reason": f"{cmd[0]} produced non-JSON output"}

    return {"checkout_path": checkout_path, "ecosystem": ecosystem, "skipped": False,
             "vulnerabilities": _normalize_vulnerabilities(ecosystem, raw)}


def _normalize_vulnerabilities(ecosystem: str, raw: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if ecosystem == "python":
        # pip-audit --format json:
        # {"dependencies": [{"name","version","vulns": [{"id","fix_versions","description"}]}]}
        for dep in raw.get("dependencies", []) or []:
            for vuln in dep.get("vulns", []) or []:
                items.append({
                    "product": dep.get("name", ""), "version": dep.get("version", ""),
                    "id": vuln.get("id", ""), "detail": vuln.get("description", ""), "severity": "medium",
                })
    elif ecosystem == "npm":
        # npm audit --json (v7+): {"vulnerabilities": {"<pkg>": {"severity", "via": [...]}}}
        for name, entry in (raw.get("vulnerabilities") or {}).items():
            if not isinstance(entry, dict):
                continue
            severity = str(entry.get("severity", "medium")).lower()
            if severity not in {"low", "medium", "high", "critical"}:
                severity = "medium"
            via = entry.get("via") or []
            detail = "; ".join(v.get("title", "") for v in via if isinstance(v, dict) and v.get("title"))
            vuln_id = ",".join(str(v.get("source", "")) for v in via if isinstance(v, dict) and v.get("source")) or name
            items.append({
                "product": name, "version": entry.get("range", ""),
                "id": vuln_id, "detail": detail, "severity": severity,
            })
    return items
