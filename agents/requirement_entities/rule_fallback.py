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

"""Rule-based data-model/flow extraction -- no LLM required.

This is a much cruder floor than agents/requirement_quality/rule_fallback.py's
structural checks: it can't tell a real domain noun ("Order") from an
incidentally-capitalized word, only spot capitalized words and filter out the
most common false positives (sentence-starters, requirement boilerplate).
Flows are only guessed for `document`-sourced requirements with a real file
path to derive a name from -- `github`-sourced requirements (origin_id is
just an issue number) get an empty flows list rather than a fabricated one.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from agents.common.models import ModelDependency, Requirement, RequirementEntities

# Capitalized words that are sentence-starters or requirement boilerplate, not
# domain entities -- excluded so "The user logs in." doesn't yield "The".
_STOPWORDS = {
    "The", "This", "That", "These", "Those", "When", "If", "As", "Given",
    "Verify", "Ensure", "Check", "Confirm", "After", "Before", "Should",
    "Then", "And", "For", "With", "From", "Into", "Onto", "Via", "Using",
    "A", "An", "It", "They", "Once", "Also", "Note",
}

# Matches a capitalized word whose remaining letters are lowercase -- filters
# out ALL-CAPS acronyms (SSO, API, URL) by construction, not just a stoplist.
_CAPITALIZED_WORD = re.compile(r"\b[A-Z][a-z]{2,}\b")

# Explicit typed edges: "Order depends on Payment" / "Checkout requires Cart".
_DEPENDS_ON = re.compile(
    r"\b([A-Z][A-Za-z0-9_]*)\s+(?:depends\s+on|requires|uses|embeds)\s+([A-Z][A-Za-z0-9_]*)\b",
    re.IGNORECASE,
)


def _candidate_data_models(text: str) -> list[str]:
    seen: list[str] = []
    for match in _CAPITALIZED_WORD.finditer(text):
        word = match.group(0)
        if word in _STOPWORDS or word in seen:
            continue
        seen.append(word)
    return seen[:6]


def _candidate_dependencies(text: str) -> list[ModelDependency]:
    deps: list[ModelDependency] = []
    seen: set[tuple[str, str]] = set()
    for match in _DEPENDS_ON.finditer(text):
        source, target = match.group(1), match.group(2)
        if source.lower() == target.lower():
            continue
        key = (source, target)
        if key in seen:
            continue
        seen.add(key)
        deps.append(ModelDependency(source=source, target=target, relation="depends_on"))
    return deps[:8]


def _guessed_flow(req: Requirement) -> list[str]:
    if req.source_type != "document" or not req.origin_id:
        return []
    stem = PurePosixPath(req.origin_id).stem
    if not stem or stem == req.origin_id.rstrip("/"):
        return []  # no real path structure to derive a name from
    words = re.split(r"[-_\s]+", stem)
    words = [w for w in words if w]
    if not words:
        return []
    return [" ".join(w.capitalize() for w in words)]


def extract_requirement_entities_rule_based(req: Requirement) -> RequirementEntities:
    haystack = f"{req.title} {req.description}"
    models = _candidate_data_models(haystack)
    deps = _candidate_dependencies(haystack)
    for dep in deps:
        for name in (dep.source, dep.target):
            if name not in models and name not in _STOPWORDS:
                models.append(name)
    return RequirementEntities(
        requirement_id=req.id,
        data_models=models[:8],
        flows=_guessed_flow(req),
        model_dependencies=deps,
    )
