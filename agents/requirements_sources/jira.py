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

"""Jira-like ticket source: JSON export files and optional REST API."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def _issue_to_markdown(issue: dict[str, Any]) -> str:
    key = str(issue.get("key") or issue.get("id") or "TICKET")
    fields = issue.get("fields") if isinstance(issue.get("fields"), dict) else issue
    summary = str(fields.get("summary") or fields.get("title") or key)
    description = fields.get("description") or fields.get("body") or ""
    if isinstance(description, dict):
        # Atlassian document format — flatten text nodes crudely
        description = _adf_to_text(description)
    labels = fields.get("labels") or issue.get("labels") or []
    if isinstance(labels, str):
        labels = [labels]
    label_line = ", ".join(str(x) for x in labels) if labels else ""
    parts = [f"# {key}: {summary}", ""]
    if label_line:
        parts.append(f"Labels: {label_line}")
        parts.append("")
    parts.append(str(description).strip())
    parts.append("")
    return "\n".join(parts)


def _adf_to_text(node: Any) -> str:
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        if node.get("type") == "text":
            return str(node.get("text") or "")
        bits = [_adf_to_text(c) for c in node.get("content") or []]
        return "\n".join(b for b in bits if b)
    if isinstance(node, list):
        return "\n".join(_adf_to_text(x) for x in node)
    return ""


def load_json_export(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    issues: list[dict[str, Any]]
    if isinstance(data, list):
        issues = [x for x in data if isinstance(x, dict)]
    elif isinstance(data, dict) and isinstance(data.get("issues"), list):
        issues = [x for x in data["issues"] if isinstance(x, dict)]
    elif isinstance(data, dict):
        issues = [data]
    else:
        raise ValueError("JSON export must be an issue object, list, or {issues: [...]}")
    return [_issue_to_markdown(i) for i in issues]


def fetch_issue_rest(key: str) -> str:
    base = (os.environ.get("JIRA_BASE_URL") or os.environ.get("JIRA_URL") or "").rstrip("/")
    token = os.environ.get("JIRA_API_TOKEN") or os.environ.get("JIRA_TOKEN") or ""
    user = os.environ.get("JIRA_USER") or os.environ.get("JIRA_EMAIL") or ""
    if not base or not token:
        raise RuntimeError("JIRA_BASE_URL and JIRA_API_TOKEN required for live Jira fetch")
    url = f"{base}/rest/api/2/issue/{urllib.parse.quote(key)}"
    req = urllib.request.Request(url, method="GET")
    req.add_header("Accept", "application/json")
    if user:
        import base64

        auth = base64.b64encode(f"{user}:{token}".encode()).decode()
        req.add_header("Authorization", f"Basic {auth}")
    else:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:  # nosec B310 — operator-configured URL
        payload = json.loads(resp.read().decode("utf-8"))
    return _issue_to_markdown(payload)


def load(
    *,
    issue_keys: list[str] | None = None,
    export_paths: list[str] | None = None,
) -> tuple[list[str], list[str], list[str]]:
    """Returns (spec_contents, labels_for_paths, errors)."""
    contents: list[str] = []
    labels: list[str] = []
    errors: list[str] = []
    for raw in export_paths or []:
        p = Path(raw)
        if not p.exists():
            errors.append(f"{raw}: not found")
            continue
        try:
            specs = load_json_export(p)
            contents.extend(specs)
            labels.extend([f"{p}#{i}" for i in range(len(specs))])
        except Exception as exc:
            errors.append(f"{raw}: {exc}")
    for key in issue_keys or []:
        key = key.strip()
        if not key:
            continue
        try:
            contents.append(fetch_issue_rest(key))
            labels.append(f"jira:{key}")
        except (RuntimeError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as exc:
            errors.append(f"{key}: {exc}")
    return contents, labels, errors
