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

"""Unit tests for MissionControlStore's requirement persistence/versioning
(schema v3: requirements, requirement_versions, requirement_test_links)."""

from __future__ import annotations

import threading

from orchestrator.persistence.store import MissionControlStore


def _content(description: str = "the login page loads") -> dict:
    return {
        "title": "Login page loads",
        "description": description,
        "priority": "high",
        "steps": [{"action": "navigate", "target": "/login"}],
        "tags": ["smoke"],
    }


def test_upsert_requirement_creates_version_one(tmp_path):
    store = MissionControlStore(tmp_path / "req.db")
    result = store.upsert_requirement(
        "req-login",
        source_type="github",
        origin_id="issue-42.md",
        title="Login page loads",
        content=_content(),
        quality_score=88.0,
    )
    assert result["is_new_version"] is True
    assert result["previous_version"] is None
    assert result["latest_version"] == 1
    assert result["quality_score"] == 88.0


def test_upsert_requirement_same_content_is_a_noop_version(tmp_path):
    store = MissionControlStore(tmp_path / "req.db")
    store.upsert_requirement(
        "req-login", source_type="github", origin_id="issue-42.md",
        title="Login page loads", content=_content(),
    )
    second = store.upsert_requirement(
        "req-login", source_type="github", origin_id="issue-42.md",
        title="Login page loads", content=_content(),
    )
    assert second["is_new_version"] is False
    assert second["latest_version"] == 1
    assert len(store.requirement_history("req-login")) == 1


def test_upsert_requirement_changed_content_creates_new_version(tmp_path):
    store = MissionControlStore(tmp_path / "req.db")
    store.upsert_requirement(
        "req-login", source_type="github", origin_id="issue-42.md",
        title="Login page loads", content=_content("the login page loads"),
    )
    second = store.upsert_requirement(
        "req-login", source_type="github", origin_id="issue-42.md",
        title="Login page loads", content=_content("the login page loads and shows an SSO button"),
    )
    assert second["is_new_version"] is True
    assert second["previous_version"] == 1
    assert second["latest_version"] == 2
    history = store.requirement_history("req-login")
    assert [item["version"] for item in history] == [1, 2]
    assert history[1]["content"]["description"] != history[0]["content"]["description"]


def test_get_requirement_returns_latest_content_and_issues(tmp_path):
    store = MissionControlStore(tmp_path / "req.db")
    store.upsert_requirement(
        "req-login", source_type="document", origin_id="spec.pdf",
        title="Login page loads", content=_content(),
        quality_score=40.0,
        quality_issues=[{"kind": "vague_language", "severity": "medium", "message": "too vague"}],
    )
    fetched = store.get_requirement("req-login")
    assert fetched is not None
    assert fetched["source_type"] == "document"
    assert fetched["content"]["title"] == "Login page loads"
    assert fetched["quality_issues"][0]["kind"] == "vague_language"


def test_get_requirement_missing_returns_none(tmp_path):
    store = MissionControlStore(tmp_path / "req.db")
    assert store.get_requirement("nope") is None


def test_list_requirements(tmp_path):
    store = MissionControlStore(tmp_path / "req.db")
    store.upsert_requirement(
        "req-a", source_type="github", origin_id=None, title="A", content=_content("a")
    )
    store.upsert_requirement(
        "req-b", source_type="github", origin_id=None, title="B", content=_content("b")
    )
    items = store.list_requirements()
    assert {item["id"] for item in items} == {"req-a", "req-b"}


def test_link_requirement_test_and_impact_lookup(tmp_path):
    store = MissionControlStore(tmp_path / "req.db")
    store.upsert_requirement(
        "req-login", source_type="github", origin_id="issue-42.md",
        title="Login page loads", content=_content("v1"),
    )
    store.link_requirement_test("req-login", "tests/generated/login.spec.ts")
    assert store.linked_tests("req-login", 1) == ["tests/generated/login.spec.ts"]

    # Requirement changes -> version 2. The v1-linked test is still
    # retrievable by its own version number, which is exactly what impact
    # analysis needs: "which tests traced to the version that just changed."
    store.upsert_requirement(
        "req-login", source_type="github", origin_id="issue-42.md",
        title="Login page loads", content=_content("v2, now with SSO"),
    )
    assert store.linked_tests("req-login", 1) == ["tests/generated/login.spec.ts"]
    assert store.linked_tests("req-login", 2) == []


def test_data_models_and_flows_round_trip_through_get_and_history(tmp_path):
    store = MissionControlStore(tmp_path / "req.db")
    store.upsert_requirement(
        "req-checkout", source_type="document", origin_id="specs/checkout.md",
        title="Apply discount", content=_content("v1"),
        data_models=["Order", "Payment"], flows=["Checkout"],
    )
    fetched = store.get_requirement("req-checkout")
    assert fetched is not None
    assert fetched["data_models"] == ["Order", "Payment"]
    assert fetched["flows"] == ["Checkout"]

    history = store.requirement_history("req-checkout")
    assert history[0]["data_models"] == ["Order", "Payment"]
    assert history[0]["flows"] == ["Checkout"]


def test_data_models_default_to_empty_list_when_not_provided(tmp_path):
    store = MissionControlStore(tmp_path / "req.db")
    store.upsert_requirement(
        "req-login", source_type="github", origin_id="issue-42.md",
        title="Login page loads", content=_content(),
    )
    fetched = store.get_requirement("req-login")
    assert fetched is not None
    assert fetched["data_models"] == []
    assert fetched["flows"] == []


def test_requirement_impact_graph_groups_by_shared_data_model_and_flow(tmp_path):
    store = MissionControlStore(tmp_path / "req.db")
    store.upsert_requirement(
        "req-checkout", source_type="document", origin_id="specs/checkout.md",
        title="Apply discount", content=_content("checkout v1"),
        data_models=["Order", "Payment"], flows=["Checkout"],
    )
    store.link_requirement_test("req-checkout", "tests/e2e/checkout.spec.ts")
    store.upsert_requirement(
        "req-order-history", source_type="document", origin_id="specs/orders.md",
        title="View past orders", content=_content("orders v1"),
        data_models=["Order"], flows=["Order history"],
    )
    store.link_requirement_test("req-order-history", "tests/e2e/orders.spec.ts")
    # A requirement with no entities must not show up in any group.
    store.upsert_requirement(
        "req-untagged", source_type="github", origin_id="7",
        title="Homepage returns 200", content=_content("untagged"),
    )

    graph = store.requirement_impact_graph()

    assert set(graph["data_models"]["Order"]) == {"req-checkout", "req-order-history"}
    assert graph["data_models"]["Payment"] == ["req-checkout"]
    assert "req-untagged" not in graph["data_models"].get("Order", [])
    assert graph["flows"]["Checkout"]["requirements"] == ["req-checkout"]
    assert graph["flows"]["Checkout"]["tests"] == ["tests/e2e/checkout.spec.ts"]
    assert graph["flows"]["Order history"]["tests"] == ["tests/e2e/orders.spec.ts"]
    # Co-occurrence edge: Order ↔ Payment on the same requirement
    edges = {(e["a"], e["b"]): e["weight"] for e in graph["model_edges"]}
    assert edges[("Order", "Payment")] == 1
    assert graph["model_dependencies"] == []


def test_requirement_impact_graph_typed_dependencies(tmp_path):
    store = MissionControlStore(tmp_path / "req.db")
    store.upsert_requirement(
        "req-order", source_type="document", origin_id="specs/order.md",
        title="Order depends on Payment", content=_content("order v1"),
        data_models=["Order", "Payment"],
        model_dependencies=[
            {"source": "Order", "target": "Payment", "relation": "depends_on"},
        ],
    )
    graph = store.requirement_impact_graph()
    assert graph["model_dependencies"] == [
        {
            "source": "Order",
            "target": "Payment",
            "relation": "depends_on",
            "requirement_id": "req-order",
        }
    ]


def test_requirement_impact_graph_empty_when_nothing_tagged(tmp_path):
    store = MissionControlStore(tmp_path / "req.db")
    store.upsert_requirement(
        "req-login", source_type="github", origin_id="issue-42.md",
        title="Login page loads", content=_content(),
    )
    assert store.requirement_impact_graph() == {
        "data_models": {},
        "flows": {},
        "model_edges": [],
        "model_dependencies": [],
    }

def test_link_requirement_test_unknown_requirement_is_a_noop(tmp_path):
    store = MissionControlStore(tmp_path / "req.db")
    store.link_requirement_test("does-not-exist", "tests/generated/x.spec.ts")
    assert store.linked_tests("does-not-exist", 1) == []


def test_requirements_migration_is_idempotent(tmp_path):
    db_path = tmp_path / "req.db"
    MissionControlStore(db_path)
    MissionControlStore(db_path)  # second migrate() pass must not error


def test_upsert_requirement_is_safe_under_concurrent_first_inserts(tmp_path):
    """Two overlapping pipeline runs (a schedule and a webhook-triggered run,
    say) can both call upsert_requirement() for the same brand-new id at
    the same time. Without an explicit write lock, both read "doesn't exist
    yet" and both attempt the INSERT, raising an unhandled IntegrityError on
    `requirements.id`'s own PRIMARY KEY -- reproduced live before this test
    was added. BEGIN IMMEDIATE (mirroring claim_job()'s existing pattern in
    this same file) serializes them instead."""
    store = MissionControlStore(tmp_path / "req.db")
    errors: list[Exception] = []

    def upsert() -> None:
        try:
            store.upsert_requirement(
                "req-race", source_type="github", origin_id="issue-1.md",
                title="Race test", content=_content("same content every time"),
            )
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=upsert) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    assert len(store.requirement_history("req-race")) == 1
