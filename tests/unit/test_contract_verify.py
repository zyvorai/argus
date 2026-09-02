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

"""Unit tests for agents/contract_verify/engine.py -- HAR-derived consumer
contract verification (not Pact; see the module docstring)."""

from __future__ import annotations

import httpx

from agents.contract_verify.engine import derive_expectations


def _har(entries: list[dict]) -> dict:
    return {"log": {"version": "1.2", "entries": entries}}


def _entry(method: str, url: str, status: int, mime_type: str, text: str | None = None,
           encoding: str | None = None) -> dict:
    content: dict = {"mimeType": mime_type}
    if text is not None:
        content["text"] = text
    if encoding:
        content["encoding"] = encoding
    return {"request": {"method": method, "url": url}, "response": {"status": status, "content": content}}


# -- derive_expectations ---------------------------------------------------

def test_derives_one_expectation_per_json_entry():
    har = _har([
        _entry("GET", "https://api.x.io/users/1", 200, "application/json", '{"id": 1, "active": true}'),
        _entry("GET", "https://api.x.io/style.css", 200, "text/css", "body{}"),
    ])
    exps = derive_expectations(har)
    assert len(exps) == 1
    assert exps[0]["method"] == "GET"
    assert exps[0]["path"] == "/users/1"
    assert exps[0]["expected_status"] == 200
    assert exps[0]["required_keys"] == {"id": "number", "active": "boolean"}


def test_dedups_repeated_method_and_path_keeping_first():
    har = _har([
        _entry("GET", "https://api.x.io/users/1?verbose=1", 200, "application/json", '{"id": 1}'),
        _entry("GET", "https://api.x.io/users/1?verbose=0", 200, "application/json", '{"id": 1, "extra": true}'),
    ])
    exps = derive_expectations(har)
    assert len(exps) == 1
    assert exps[0]["required_keys"] == {"id": "number"}  # from the first occurrence only


def test_skips_non_json_entries_entirely():
    har = _har([_entry("GET", "https://x.io/logo.png", 200, "image/png")])
    assert derive_expectations(har) == []


def test_skips_base64_encoded_bodies_without_crashing():
    har = _har([_entry("GET", "https://x.io/data", 200, "application/json", "aGVsbG8=", encoding="base64")])
    exps = derive_expectations(har)
    assert exps[0]["required_keys"] == {}  # couldn't decode -- no keys asserted, not an error


def test_respects_max_endpoints_cap():
    entries = [_entry("GET", f"https://x.io/e{i}", 200, "application/json", "{}") for i in range(5)]
    exps = derive_expectations(_har(entries), max_endpoints=2)
    assert len(exps) == 2


def test_empty_har_yields_no_expectations():
    assert derive_expectations({"log": {"entries": []}}) == []


# -- verify_expectations ----------------------------------------------------

def test_verify_passes_when_live_response_matches():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"id": 1, "active": True})

    exp = [{"method": "GET", "path": "/users/1", "query": "", "expected_status": 200,
            "expected_content_type": "application/json", "required_keys": {"id": "number", "active": "boolean"}}]
    results = _verify_with_transport(exp, handler)
    assert results[0]["ok"] is True


def test_verify_flags_status_mismatch():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"id": 1})

    exp = [{"method": "GET", "path": "/users/1", "query": "", "expected_status": 200,
            "expected_content_type": "application/json", "required_keys": {}}]
    results = _verify_with_transport(exp, handler)
    assert results[0]["ok"] is False
    assert "status 500" in results[0]["detail"]


def test_verify_flags_missing_required_key():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"id": 1})  # "email" missing

    exp = [{"method": "GET", "path": "/users/1", "query": "", "expected_status": 200,
            "expected_content_type": "application/json", "required_keys": {"id": "number", "email": "string"}}]
    results = _verify_with_transport(exp, handler)
    assert results[0]["ok"] is False
    assert "missing required key 'email'" in results[0]["detail"]


def test_verify_flags_type_change():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"id": "not-a-number"})

    exp = [{"method": "GET", "path": "/users/1", "query": "", "expected_status": 200,
            "expected_content_type": "application/json", "required_keys": {"id": "number"}}]
    results = _verify_with_transport(exp, handler)
    assert results[0]["ok"] is False
    assert "type string != expected number" in results[0]["detail"]


def test_verify_handles_request_failure_gracefully():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    exp = [{"method": "GET", "path": "/users/1", "query": "", "expected_status": 200,
            "expected_content_type": "application/json", "required_keys": {}}]
    results = _verify_with_transport(exp, handler)
    assert results[0]["ok"] is False
    assert "request failed" in results[0]["detail"]


def _verify_with_transport(expectations, handler):
    """verify_expectations() constructs its own httpx.Client internally, so
    route it through a MockTransport via a thin subclass swap."""
    import agents.contract_verify.engine as engine_module

    real_client = httpx.Client

    class _MockClient(real_client):
        def __init__(self, *args, **kwargs):
            kwargs.pop("verify", None)
            super().__init__(*args, transport=httpx.MockTransport(handler), **kwargs)

    import httpx as httpx_module

    original = httpx_module.Client
    httpx_module.Client = _MockClient
    try:
        return engine_module.verify_expectations("https://api.x.io", expectations)
    finally:
        httpx_module.Client = original
