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

"""Data-model/flow extraction agent -- the grouping key behind impact
analysis (see ROADMAP.md's "Business-flow/data/automation-level impact
analysis" and RequirementEntities' docstring)."""

from __future__ import annotations

import json
import os
import re

from langchain_core.messages import HumanMessage, SystemMessage

from agents.common.llm import LLMConfigError, content_to_text, get_llm, load_prompt
from agents.common.models import Requirement, RequirementEntities
from agents.requirement_entities.rule_fallback import extract_requirement_entities_rule_based


def _extract_json(text: str) -> dict:
    text = text.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence_match:
        text = fence_match.group(1)
    return json.loads(text)


def _llm_available() -> bool:
    provider = os.environ.get("LLM_PROVIDER", "openai").lower()
    key_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "azure": "AZURE_OPENAI_API_KEY",
    }
    if provider == "ollama":
        return True
    key = key_map.get(provider, "OPENAI_API_KEY")
    return bool(os.environ.get(key))


def extract_requirement_entities(req: Requirement) -> RequirementEntities:
    """Names the data models and business flow a requirement touches -- LLM
    when configured, a much cruder rule-based fallback otherwise (mirrors
    agents/requirement_quality/agent.py's fallback shape)."""
    if not _llm_available():
        return extract_requirement_entities_rule_based(req)

    try:
        llm = get_llm()
        system = load_prompt("requirement_entities")
        payload = {
            "title": req.title,
            "description": req.description,
            "steps": [step.model_dump() for step in req.steps],
            "tags": req.tags,
        }
        response = llm.invoke(
            [
                SystemMessage(content=system),
                HumanMessage(content=f"Extract entities from this requirement:\n\n{json.dumps(payload, indent=2)}"),
            ]
        )
        raw = _extract_json(content_to_text(response.content))
        from agents.common.models import ModelDependency

        return RequirementEntities(
            requirement_id=req.id,
            data_models=[str(m) for m in raw.get("data_models", [])],
            flows=[str(f) for f in raw.get("flows", [])],
            model_dependencies=[
                ModelDependency(
                    source=str(d.get("source") or "").strip(),
                    target=str(d.get("target") or "").strip(),
                    relation=str(d.get("relation") or "depends_on"),
                )
                for d in (raw.get("model_dependencies") or [])
                if isinstance(d, dict) and d.get("source") and d.get("target")
            ],
        )
    except (LLMConfigError, json.JSONDecodeError, ValueError, KeyError, Exception):
        return extract_requirement_entities_rule_based(req)
