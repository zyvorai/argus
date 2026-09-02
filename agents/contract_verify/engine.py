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

"""Consumer-driven contract verification -- the honest, HAR-derived slice,
not Pact. No broker, no publish/subscribe, no contract versioning, no
cross-team consumer/provider matrix, no "can-i-deploy" gating. "Derive
expectations from one recorded consumer interaction set, verify a live
provider still matches them" -- an on-ramp, not the destination (see
ROADMAP.md).

Deliberately rule-based, not LLM-driven: there's no ambiguity to resolve,
just a HAR (standard HAR 1.2 -- `log.entries[]`, each with `request`/
`response`) to read.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

# Only requests that look like API calls -- not the HTML/CSS/JS/image noise
# a full-page HAR recording also captures.
_JSON_CONTENT_TYPE = "application/json"


def _infer_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):  # must precede int -- bool is an int subclass
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "unknown"


def derive_expectations(har: dict[str, Any], *, max_endpoints: int = 60) -> list[dict[str, Any]]:
    """One expectation per unique (method, path) pair, in first-seen order,
    derived only from entries whose recorded response looks like a JSON API
    response. Query strings are replayed verbatim, not treated as part of
    the dedup key (repeated calls with different query values collapse to
    one expectation from the first occurrence)."""
    entries = ((har or {}).get("log") or {}).get("entries") or []
    seen: dict[tuple[str, str], dict[str, Any]] = {}

    for entry in entries:
        request = entry.get("request") or {}
        response = entry.get("response") or {}
        method = (request.get("method") or "").upper()
        url = request.get("url") or ""
        if not method or not url:
            continue

        content = response.get("content") or {}
        mime_type = (content.get("mimeType") or "").split(";")[0].strip()
        if mime_type != _JSON_CONTENT_TYPE:
            continue  # not an API-shaped response -- skip static assets/HTML/etc.

        parts = urlsplit(url)
        key = (method, parts.path)
        if key in seen:
            continue

        required_keys: dict[str, str] = {}
        text = content.get("text")
        if isinstance(text, str) and not content.get("encoding"):  # skip base64-encoded bodies
            import json

            try:
                body = json.loads(text)
            except (json.JSONDecodeError, ValueError):
                body = None
            if isinstance(body, dict):
                required_keys = {k: _infer_type(v) for k, v in body.items()}

        seen[key] = {
            "method": method,
            "path": parts.path,
            "query": parts.query,
            "expected_status": response.get("status"),
            "expected_content_type": mime_type,
            "required_keys": required_keys,
        }
        if len(seen) >= max_endpoints:
            break

    return list(seen.values())


def verify_expectations(
    base_url: str, expectations: list[dict[str, Any]], *, insecure: bool = False, timeout_s: float = 15,
) -> list[dict[str, Any]]:
    import httpx

    results: list[dict[str, Any]] = []
    with httpx.Client(verify=not insecure, timeout=timeout_s, follow_redirects=True) as client:
        for exp in expectations:
            name = f"{exp['method']} {exp['path']}"
            url = base_url.rstrip("/") + exp["path"]
            if exp.get("query"):
                url += "?" + exp["query"]

            try:
                response = client.request(exp["method"], url)
            except Exception as exc:
                results.append({"name": name, "method": exp["method"], "path": exp["path"],
                                 "ok": False, "detail": f"request failed: {str(exc)[:200]}"})
                continue

            issues: list[str] = []
            if exp.get("expected_status") is not None and response.status_code != exp["expected_status"]:
                issues.append(f"status {response.status_code} != expected {exp['expected_status']}")

            actual_ct = response.headers.get("content-type", "").split(";")[0].strip()
            if exp.get("expected_content_type") and actual_ct != exp["expected_content_type"]:
                issues.append(f"content-type {actual_ct!r} != expected {exp['expected_content_type']!r}")

            if exp.get("required_keys"):
                try:
                    body = response.json()
                except Exception:
                    body = None
                if not isinstance(body, dict):
                    issues.append("response body is not a JSON object")
                else:
                    for key, expected_type in exp["required_keys"].items():
                        if key not in body:
                            issues.append(f"missing required key '{key}'")
                        elif _infer_type(body[key]) != expected_type:
                            issues.append(f"key '{key}' type {_infer_type(body[key])} != expected {expected_type}")

            results.append({
                "name": name, "method": exp["method"], "path": exp["path"],
                "ok": not issues, "detail": "; ".join(issues),
            })

    return results
