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

"""HTTP-level tests for GET /api/v2/requirements{,/{id},/{id}/history} --
the read-only surface for the durable, versioned requirement store.

`get_store()` is a process-wide singleton cached on first call (see
orchestrator/persistence/store.py), so — matching the existing
tests/unit/test_scheduler.py pattern — these tests monkeypatch the route
module's own `get_store` reference to a fresh per-test store rather than
relying on `ZYVOR_STATE_DB`, which would arrive too late for tests that
run after the singleton is already cached.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from orchestrator.dashboard import v2_routes
from orchestrator.persistence.store import MissionControlStore
from orchestrator.webhook import create_app


def _client_with_store(monkeypatch, store: MissionControlStore) -> TestClient:
    monkeypatch.setattr(v2_routes, "get_store", lambda: store)
    return TestClient(create_app())


def test_list_requirements_empty_by_default(tmp_path, monkeypatch):
    store = MissionControlStore(tmp_path / "req.db")
    client = _client_with_store(monkeypatch, store)

    resp = client.get("/api/v2/requirements")
    assert resp.status_code == 200
    assert resp.json() == {"requirements": []}


def test_list_and_get_requirement(tmp_path, monkeypatch):
    store = MissionControlStore(tmp_path / "req.db")
    store.upsert_requirement(
        "req-login",
        source_type="document",
        origin_id="spec.md",
        title="Login page loads",
        content={"description": "v1"},
        quality_score=90.0,
        quality_issues=[],
    )
    client = _client_with_store(monkeypatch, store)

    listed = client.get("/api/v2/requirements").json()["requirements"]
    assert len(listed) == 1
    assert listed[0]["id"] == "req-login"

    detail = client.get("/api/v2/requirements/req-login")
    assert detail.status_code == 200
    body = detail.json()
    assert body["content"]["description"] == "v1"
    assert body["quality_score"] == 90.0


def test_get_requirement_404_when_missing(tmp_path, monkeypatch):
    store = MissionControlStore(tmp_path / "req.db")
    client = _client_with_store(monkeypatch, store)

    resp = client.get("/api/v2/requirements/does-not-exist")
    assert resp.status_code == 404


def test_requirement_history_returns_every_version(tmp_path, monkeypatch):
    store = MissionControlStore(tmp_path / "req.db")
    store.upsert_requirement(
        "req-login", source_type="document", origin_id="spec.md",
        title="Login page loads", content={"description": "v1"},
    )
    store.upsert_requirement(
        "req-login", source_type="document", origin_id="spec.md",
        title="Login page loads", content={"description": "v2"},
    )
    client = _client_with_store(monkeypatch, store)

    resp = client.get("/api/v2/requirements/req-login/history")
    assert resp.status_code == 200
    versions = resp.json()["versions"]
    assert [v["version"] for v in versions] == [1, 2]


def test_requirement_history_includes_linked_tests_per_version(tmp_path, monkeypatch):
    store = MissionControlStore(tmp_path / "req.db")
    store.upsert_requirement(
        "req-login", source_type="document", origin_id="spec.md",
        title="Login page loads", content={"description": "v1"},
    )
    store.link_requirement_test("req-login", "tests/e2e/login.spec.ts")
    store.upsert_requirement(
        "req-login", source_type="document", origin_id="spec.md",
        title="Login page loads", content={"description": "v2"},
    )
    store.link_requirement_test("req-login", "tests/e2e/login-v2.spec.ts")
    client = _client_with_store(monkeypatch, store)

    versions = client.get("/api/v2/requirements/req-login/history").json()["versions"]
    assert versions[0]["linked_tests"] == ["tests/e2e/login.spec.ts"]
    assert versions[1]["linked_tests"] == ["tests/e2e/login-v2.spec.ts"]
