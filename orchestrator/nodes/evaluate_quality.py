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

"""Score each parsed requirement for quality/gaps, persist it (with version
history), and surface which previously-generated tests trace to a requirement
that changed since the last run.

This is the step that turns quality scoring and requirement understanding
from "computed once and discarded" into structured, stored, and reusable —
`MissionControlStore.upsert_requirement()` only creates a new version when the
content actually changed, so re-running the pipeline against an unchanged
requirement is a no-op here, not noise.
"""

from __future__ import annotations

from agents.common.models import Requirement
from agents.requirement_entities.agent import extract_requirement_entities
from agents.requirement_quality.agent import evaluate_requirement_quality
from orchestrator.persistence.store import get_store
from orchestrator.state import PipelineState


def _content_for_hash(req: Requirement) -> dict:
    # Everything that defines "what this requirement asks for" — excludes
    # nothing meaningful, but deliberately excludes `id` (the primary key
    # already carries identity, hashing it too would be redundant).
    return {
        "title": req.title,
        "description": req.description,
        "priority": req.priority,
        "steps": [step.model_dump() for step in req.steps],
        "tags": sorted(req.tags),
    }


def evaluate_quality(state: PipelineState) -> PipelineState:
    """Score, persist, and version every requirement from this run."""
    if state.get("error"):
        return state

    requirements = state.get("requirements", [])
    store = get_store()
    quality: dict[str, dict] = {}
    impact: dict[str, list[str]] = {}

    for req in requirements:
        result = evaluate_requirement_quality(req)
        quality[req.id] = result.model_dump()
        entities = extract_requirement_entities(req)

        persisted = store.upsert_requirement(
            req.id,
            source_type=req.source_type,
            origin_id=req.origin_id,
            title=req.title,
            content=_content_for_hash(req),
            quality_score=result.score,
            quality_issues=[issue.model_dump() for issue in result.issues],
            data_models=entities.data_models,
            flows=entities.flows,
            model_dependencies=[d.model_dump() for d in entities.model_dependencies],
        )

        if persisted["is_new_version"] and persisted["previous_version"]:
            previously_linked = store.linked_tests(req.id, persisted["previous_version"])
            if previously_linked:
                impact[req.id] = previously_linked

    metadata = dict(state.get("metadata", {}))
    metadata["requirements_changed"] = len(impact)
    metadata["requirements_scored"] = len(quality)
    if quality:
        metadata["requirements_avg_quality_score"] = round(
            sum(q["score"] for q in quality.values()) / len(quality), 1
        )

    return {
        **state,
        "requirement_quality": quality,
        "requirement_impact": impact,
        "metadata": metadata,
    }
