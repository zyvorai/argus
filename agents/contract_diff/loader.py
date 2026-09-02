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

"""Resolves an OpenAPI spec reference into a parsed dict, for
agents/contract_diff/engine.py to diff. Three shapes, mirroring how
`api_contract`'s own `spec` param already overloads inline-vs-URL:

    {"openapi": "3.0.0", ...}       # inline spec, already a dict
    "https://api.example.com/openapi.json"   # fetched (SSRF-checked upstream
                                              # in orchestrator/dashboard/jobs.py's
                                              # _validate())
    "git:main:openapi.yaml"         # `git show <ref>:<path>` against this
                                     # repo's own checkout
"""

from __future__ import annotations

import json
import subprocess
from typing import Any


class SpecLoadError(ValueError):
    pass


def load_spec(ref: Any, *, insecure: bool = False) -> dict[str, Any]:
    if isinstance(ref, dict):
        return ref
    if isinstance(ref, str):
        if ref.startswith(("http://", "https://")):
            return _fetch_spec(ref, insecure=insecure)
        if ref.startswith("git:"):
            return _load_from_git(ref)
    raise SpecLoadError(
        f"unsupported spec reference: {ref!r} -- must be an inline object, "
        "an http(s) URL, or a 'git:<ref>:<path>' reference"
    )


def _fetch_spec(url: str, *, insecure: bool = False) -> dict[str, Any]:
    import httpx

    with httpx.Client(timeout=15, verify=not insecure, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
    return _parse_spec_text(response.text)


def _load_from_git(ref: str) -> dict[str, Any]:
    _, _, rest = ref.partition(":")
    gitref, _, path = rest.partition(":")
    if not gitref or not path:
        raise SpecLoadError(f"git spec reference must be 'git:<ref>:<path>', got {ref!r}")

    from orchestrator.paths import repo_root

    proc = subprocess.run(
        ["git", "show", f"{gitref}:{path}"],
        cwd=repo_root(), capture_output=True, text=True, timeout=15,
    )
    if proc.returncode != 0:
        raise SpecLoadError(f"git show {gitref}:{path} failed: {(proc.stderr or '')[:200]}")
    return _parse_spec_text(proc.stdout)


def _parse_spec_text(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        import yaml

        parsed = yaml.safe_load(text)
    if not isinstance(parsed, dict):
        raise SpecLoadError("spec did not parse to a JSON/YAML object")
    return parsed
