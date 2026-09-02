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

"""OpenAPI breaking-change diff -- pure Python, no subprocess tool (unlike
`zyvor-diff`'s Rust pixel-diffing, this isn't CPU-bound enough to warrant one).

First slice, deliberately: only JSON Schema primitives (type/required/enum) on
request parameters and `application/json` response bodies are compared.
Explicitly NOT handled (see ROADMAP.md) -- `oneOf`/`allOf`/`discriminator`
semantic diffing, vendor extensions, and `$ref`s that point outside the
document being diffed (external file/URL refs).
"""

from __future__ import annotations

from typing import Any

BREAKING = "breaking"
NON_BREAKING = "non_breaking"

_HTTP_METHODS = ("get", "put", "post", "delete", "options", "head", "patch", "trace")


def _change(classification: str, rule: str, where: str, message: str) -> dict[str, Any]:
    return {"classification": classification, "rule": rule, "where": where, "message": message}


def _endpoint_key(path: str, method: str) -> str:
    return f"{method.upper()} {path}"


def _resolve_local_ref(spec: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        # External $ref (another file/URL) -- explicitly out of scope for this
        # first slice; treat as unresolvable rather than guessing.
        return {}
    node: Any = spec
    for part in ref[2:].split("/"):
        node = node.get(part, {}) if isinstance(node, dict) else {}
    return node if isinstance(node, dict) else {}


def _resolve_schema(spec: dict[str, Any], schema: dict[str, Any] | None, *, depth: int = 0) -> dict[str, Any]:
    if not schema or depth > 10:
        return {}
    if "$ref" in schema:
        return _resolve_schema(spec, _resolve_local_ref(spec, schema["$ref"]), depth=depth + 1)
    return schema


def _extract_json_schema(response: dict[str, Any] | None) -> dict[str, Any] | None:
    content = (response or {}).get("content", {}) or {}
    media = content.get("application/json") or {}
    return media.get("schema")


def diff_specs(spec_a: dict[str, Any], spec_b: dict[str, Any]) -> list[dict[str, Any]]:
    """Returns a flat list of `_change(...)` dicts. `spec_a` is treated as the
    baseline (e.g. what consumers built against), `spec_b` as the candidate
    (e.g. what's about to ship) -- classification is from spec_a's consumers'
    point of view."""
    changes: list[dict[str, Any]] = []
    paths_a = spec_a.get("paths", {}) or {}
    paths_b = spec_b.get("paths", {}) or {}

    for path, methods_a in paths_a.items():
        if not isinstance(methods_a, dict):
            continue
        methods_b = paths_b.get(path)
        if not isinstance(methods_b, dict):
            changes.append(_change(BREAKING, "removed-endpoint", _endpoint_key(path, "*"), f"endpoint {path} removed"))
            continue
        for method in _HTTP_METHODS:
            if method not in methods_a:
                continue
            if method not in methods_b:
                changes.append(_change(BREAKING, "removed-endpoint", _endpoint_key(path, method),
                                        f"{method.upper()} {path} removed"))
                continue
            changes.extend(_diff_operation(spec_a, spec_b, path, method, methods_a[method], methods_b[method]))

    for path, methods_b in paths_b.items():
        if not isinstance(methods_b, dict):
            continue
        methods_a = paths_a.get(path)
        for method in _HTTP_METHODS:
            if method not in methods_b:
                continue
            if not isinstance(methods_a, dict) or method not in methods_a:
                changes.append(_change(NON_BREAKING, "added-endpoint", _endpoint_key(path, method),
                                        f"{method.upper()} {path} added"))

    return changes


def _diff_operation(
    spec_a: dict[str, Any], spec_b: dict[str, Any], path: str, method: str,
    op_a: dict[str, Any], op_b: dict[str, Any],
) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    where = _endpoint_key(path, method)

    params_a = {p["name"]: p for p in op_a.get("parameters", []) or [] if isinstance(p, dict) and "name" in p}
    params_b = {p["name"]: p for p in op_b.get("parameters", []) or [] if isinstance(p, dict) and "name" in p}

    for name, pa in params_a.items():
        pb = params_b.get(name)
        if pb is None:
            # A consumer who stops sending a now-gone param isn't broken by it.
            changes.append(_change(NON_BREAKING, "removed-param", where, f"parameter '{name}' removed"))
            continue
        if not pa.get("required") and pb.get("required"):
            changes.append(_change(BREAKING, "param-now-required", where, f"parameter '{name}' is now required"))
        type_a = (pa.get("schema") or {}).get("type")
        type_b = (pb.get("schema") or {}).get("type")
        if type_a and type_b and type_a != type_b:
            changes.append(_change(BREAKING, "param-type-changed", where,
                                    f"parameter '{name}' type changed {type_a} -> {type_b}"))

    for name, pb in params_b.items():
        if name in params_a:
            continue
        required = bool(pb.get("required"))
        changes.append(_change(
            BREAKING if required else NON_BREAKING,
            "new-required-param" if required else "new-optional-param",
            where, f"parameter '{name}' added{' (required)' if required else ''}",
        ))

    responses_a = op_a.get("responses", {}) or {}
    responses_b = op_b.get("responses", {}) or {}
    for status, resp_a in responses_a.items():
        if status not in responses_b:
            changes.append(_change(BREAKING, "removed-response-code", where, f"response {status} removed"))
            continue
        changes.extend(_diff_response_schema(spec_a, spec_b, where, status, resp_a, responses_b[status]))
    for status in responses_b:
        if status not in responses_a:
            changes.append(_change(NON_BREAKING, "added-response-code", where, f"response {status} added"))

    return changes


def _diff_response_schema(
    spec_a: dict[str, Any], spec_b: dict[str, Any], where: str, status: str,
    resp_a: dict[str, Any], resp_b: dict[str, Any],
) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    schema_a = _resolve_schema(spec_a, _extract_json_schema(resp_a))
    schema_b = _resolve_schema(spec_b, _extract_json_schema(resp_b))
    if not schema_a or not schema_b:
        return changes

    props_a = schema_a.get("properties", {}) or {}
    props_b = schema_b.get("properties", {}) or {}
    where_status = f"{where} {status}"

    for name, sa in props_a.items():
        sb = props_b.get(name)
        if sb is None:
            changes.append(_change(BREAKING, "removed-field", where_status, f"response field '{name}' removed"))
            continue
        type_a, type_b = sa.get("type"), sb.get("type")
        if type_a and type_b and type_a != type_b:
            changes.append(_change(BREAKING, "field-type-changed", where_status,
                                    f"response field '{name}' type changed {type_a} -> {type_b}"))
        enum_a, enum_b = set(sa.get("enum", []) or []), set(sb.get("enum", []) or [])
        removed_enum, added_enum = enum_a - enum_b, enum_b - enum_a
        if removed_enum:
            changes.append(_change(BREAKING, "enum-value-removed", where_status,
                                    f"response field '{name}' removed enum value(s): {sorted(removed_enum)}"))
        if added_enum:
            changes.append(_change(NON_BREAKING, "enum-value-added", where_status,
                                    f"response field '{name}' added enum value(s): {sorted(added_enum)}"))

    for name in props_b:
        if name not in props_a:
            changes.append(_change(NON_BREAKING, "added-field", where_status, f"response field '{name}' added"))

    return changes
