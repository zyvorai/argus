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

"""Unit tests for agents/contract_diff/ -- the pure-Python OpenAPI
breaking-change diff engine and spec loader."""

from __future__ import annotations

import httpx
import pytest

from agents.contract_diff.engine import BREAKING, NON_BREAKING, diff_specs
from agents.contract_diff.loader import SpecLoadError, load_spec


def _spec(paths: dict) -> dict:
    return {"openapi": "3.0.0", "paths": paths}


def _op(*, params=None, responses=None) -> dict:
    return {"parameters": params or [], "responses": responses or {"200": {"description": "ok"}}}


# -- engine: endpoints --------------------------------------------------

def test_identical_specs_produce_no_changes():
    spec = _spec({"/users": {"get": _op()}})
    assert diff_specs(spec, spec) == []


def test_removed_endpoint_is_breaking():
    a = _spec({"/users": {"get": _op()}})
    b = _spec({})
    changes = diff_specs(a, b)
    assert len(changes) == 1
    assert changes[0]["classification"] == BREAKING
    assert changes[0]["rule"] == "removed-endpoint"


def test_added_endpoint_is_non_breaking():
    a = _spec({})
    b = _spec({"/users": {"get": _op()}})
    changes = diff_specs(a, b)
    assert len(changes) == 1
    assert changes[0]["classification"] == NON_BREAKING
    assert changes[0]["rule"] == "added-endpoint"


def test_removed_method_on_shared_path_is_breaking():
    a = _spec({"/users": {"get": _op(), "post": _op()}})
    b = _spec({"/users": {"get": _op()}})
    changes = diff_specs(a, b)
    assert len(changes) == 1
    assert changes[0]["where"] == "POST /users"
    assert changes[0]["classification"] == BREAKING


# -- engine: request parameters -----------------------------------------

def test_new_required_param_is_breaking():
    a = _spec({"/users": {"get": _op(params=[])}})
    b = _spec({"/users": {"get": _op(params=[{"name": "tenant", "required": True, "schema": {"type": "string"}}])}})
    changes = diff_specs(a, b)
    assert changes[0]["rule"] == "new-required-param"
    assert changes[0]["classification"] == BREAKING


def test_new_optional_param_is_non_breaking():
    a = _spec({"/users": {"get": _op(params=[])}})
    b = _spec({"/users": {"get": _op(params=[{"name": "sort", "required": False, "schema": {"type": "string"}}])}})
    changes = diff_specs(a, b)
    assert changes[0]["rule"] == "new-optional-param"
    assert changes[0]["classification"] == NON_BREAKING


def test_param_becoming_required_is_breaking():
    a = _spec({"/users": {"get": _op(params=[{"name": "id", "required": False, "schema": {"type": "string"}}])}})
    b = _spec({"/users": {"get": _op(params=[{"name": "id", "required": True, "schema": {"type": "string"}}])}})
    changes = diff_specs(a, b)
    assert changes[0]["rule"] == "param-now-required"
    assert changes[0]["classification"] == BREAKING


def test_param_type_change_is_breaking():
    a = _spec({"/users": {"get": _op(params=[{"name": "id", "schema": {"type": "string"}}])}})
    b = _spec({"/users": {"get": _op(params=[{"name": "id", "schema": {"type": "integer"}}])}})
    changes = diff_specs(a, b)
    assert changes[0]["rule"] == "param-type-changed"
    assert changes[0]["classification"] == BREAKING


def test_removed_param_is_non_breaking():
    a = _spec({"/users": {"get": _op(params=[{"name": "legacy_flag", "schema": {"type": "string"}}])}})
    b = _spec({"/users": {"get": _op(params=[])}})
    changes = diff_specs(a, b)
    assert changes[0]["rule"] == "removed-param"
    assert changes[0]["classification"] == NON_BREAKING


# -- engine: responses ----------------------------------------------------

def test_removed_response_code_is_breaking():
    a = _spec({"/users": {"get": _op(responses={"200": {}, "404": {}})}})
    b = _spec({"/users": {"get": _op(responses={"200": {}})}})
    changes = diff_specs(a, b)
    assert any(c["rule"] == "removed-response-code" and c["classification"] == BREAKING for c in changes)


def test_added_response_code_is_non_breaking():
    a = _spec({"/users": {"get": _op(responses={"200": {}})}})
    b = _spec({"/users": {"get": _op(responses={"200": {}, "429": {}})}})
    changes = diff_specs(a, b)
    assert any(c["rule"] == "added-response-code" and c["classification"] == NON_BREAKING for c in changes)


def _resp_with_schema(schema: dict) -> dict:
    return {"content": {"application/json": {"schema": schema}}}


def test_removed_response_field_is_breaking():
    a = _spec({"/users": {"get": _op(responses={
        "200": _resp_with_schema({"properties": {"id": {"type": "string"}, "email": {"type": "string"}}})})}})
    b = _spec({"/users": {"get": _op(responses={
        "200": _resp_with_schema({"properties": {"id": {"type": "string"}}})})}})
    changes = diff_specs(a, b)
    assert any(c["rule"] == "removed-field" and c["classification"] == BREAKING for c in changes)


def test_added_response_field_is_non_breaking():
    a = _spec({"/users": {"get": _op(responses={
        "200": _resp_with_schema({"properties": {"id": {"type": "string"}}})})}})
    b = _spec({"/users": {"get": _op(responses={
        "200": _resp_with_schema({"properties": {"id": {"type": "string"}, "created_at": {"type": "string"}}})})}})
    changes = diff_specs(a, b)
    assert any(c["rule"] == "added-field" and c["classification"] == NON_BREAKING for c in changes)


def test_response_field_type_change_is_breaking():
    a = _spec({"/users": {"get": _op(responses={
        "200": _resp_with_schema({"properties": {"id": {"type": "integer"}}})})}})
    b = _spec({"/users": {"get": _op(responses={
        "200": _resp_with_schema({"properties": {"id": {"type": "string"}}})})}})
    changes = diff_specs(a, b)
    assert any(c["rule"] == "field-type-changed" and c["classification"] == BREAKING for c in changes)


def test_enum_value_removed_is_breaking_added_is_non_breaking():
    a = _spec({"/orders": {"get": _op(responses={
        "200": _resp_with_schema({"properties": {"status": {"type": "string", "enum": ["open", "closed"]}}})})}})
    b = _spec({"/orders": {"get": _op(responses={
        "200": _resp_with_schema({"properties": {"status": {"type": "string", "enum": ["open", "archived"]}}})})}})
    changes = diff_specs(a, b)
    removed = [c for c in changes if c["rule"] == "enum-value-removed"]
    added = [c for c in changes if c["rule"] == "enum-value-added"]
    assert removed and removed[0]["classification"] == BREAKING
    assert added and added[0]["classification"] == NON_BREAKING


def test_local_ref_is_resolved_for_response_schema_diff():
    a = _spec({
        "/users": {"get": _op(responses={"200": _resp_with_schema({"$ref": "#/components/schemas/User"})})},
    })
    a["components"] = {"schemas": {"User": {"properties": {"id": {"type": "string"}, "email": {"type": "string"}}}}}
    b = _spec({
        "/users": {"get": _op(responses={"200": _resp_with_schema({"$ref": "#/components/schemas/User"})})},
    })
    b["components"] = {"schemas": {"User": {"properties": {"id": {"type": "string"}}}}}
    changes = diff_specs(a, b)
    assert any(c["rule"] == "removed-field" for c in changes)


def test_external_ref_is_not_resolved_and_does_not_crash():
    a = _spec({
        "/users": {"get": _op(responses={"200": _resp_with_schema({"$ref": "other-file.yaml#/User"})})},
    })
    changes = diff_specs(a, a)
    assert changes == []


# -- loader ---------------------------------------------------------------

def test_load_spec_inline_dict_passthrough():
    spec = {"openapi": "3.0.0"}
    assert load_spec(spec) is spec


def test_load_spec_rejects_malformed_git_ref():
    with pytest.raises(SpecLoadError):
        load_spec("git:main")  # missing ":<path>"


def test_load_spec_rejects_unsupported_reference():
    with pytest.raises(SpecLoadError):
        load_spec(12345)


_RealClient = httpx.Client


def test_load_spec_fetches_json_over_http(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"openapi": "3.0.0", "paths": {}})

    monkeypatch.setattr(httpx, "Client", lambda **kw: _RealClient(transport=httpx.MockTransport(handler)))
    spec = load_spec("https://api.example.com/openapi.json")
    assert spec["openapi"] == "3.0.0"


def test_load_spec_fetches_yaml_over_http(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="openapi: 3.0.0\npaths: {}\n")

    monkeypatch.setattr(httpx, "Client", lambda **kw: _RealClient(transport=httpx.MockTransport(handler)))
    spec = load_spec("https://api.example.com/openapi.yaml")
    assert spec["openapi"] == "3.0.0"


def test_load_spec_from_git_ref(monkeypatch):
    import subprocess

    def fake_run(cmd, **kwargs):
        assert cmd[:2] == ["git", "show"]
        return subprocess.CompletedProcess(cmd, 0, stdout='{"openapi": "3.0.0", "paths": {}}', stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    spec = load_spec("git:main:openapi.json")
    assert spec["openapi"] == "3.0.0"


def test_load_spec_from_git_ref_raises_on_failure(monkeypatch):
    import subprocess

    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 128, stdout="", stderr="fatal: bad revision")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(SpecLoadError):
        load_spec("git:doesnotexist:openapi.json")
