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

"""Unit tests for the evaluate_quality node — scoring, persistence, and
first-cut change-impact detection (requirement changed -> previously-linked
tests surfaced as potentially affected)."""

from __future__ import annotations

from agents.common.models import Requirement, RequirementStep
from orchestrator.nodes import evaluate_quality as evaluate_quality_module
from orchestrator.persistence.store import MissionControlStore


def _requirement(req_id: str = "req-login", description: str = "v1") -> Requirement:
    return Requirement(
        id=req_id,
        title="Login page loads",
        description=description,
        source_type="github",
        origin_id="issue-1.md",
        steps=[RequirementStep(action="navigate", target="/login")],
    )


def test_evaluate_quality_scores_and_persists(tmp_path, monkeypatch):
    store = MissionControlStore(tmp_path / "req.db")
    monkeypatch.setattr(evaluate_quality_module, "get_store", lambda: store)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    state = {"requirements": [_requirement()]}
    result = evaluate_quality_module.evaluate_quality(state)

    assert "req-login" in result["requirement_quality"]
    assert result["metadata"]["requirements_scored"] == 1
    assert result["requirement_impact"] == {}  # first time seeing it -> nothing changed yet

    persisted = store.get_requirement("req-login")
    assert persisted is not None
    assert persisted["latest_version"] == 1
    assert isinstance(persisted["data_models"], list)
    assert isinstance(persisted["flows"], list)


def test_evaluate_quality_surfaces_impact_when_requirement_changes(tmp_path, monkeypatch):
    store = MissionControlStore(tmp_path / "req.db")
    monkeypatch.setattr(evaluate_quality_module, "get_store", lambda: store)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    evaluate_quality_module.evaluate_quality({"requirements": [_requirement(description="v1")]})
    store.link_requirement_test("req-login", "tests/generated/login.spec.ts")

    result = evaluate_quality_module.evaluate_quality({"requirements": [_requirement(description="v2, adds SSO")]})

    assert result["requirement_impact"] == {"req-login": ["tests/generated/login.spec.ts"]}
    assert result["metadata"]["requirements_changed"] == 1


def test_evaluate_quality_short_circuits_on_existing_error():
    state = {"error": "upstream failed", "requirements": [_requirement()]}
    result = evaluate_quality_module.evaluate_quality(state)
    assert result == state
