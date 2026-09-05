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

"""Shared Pydantic models for the QA pipeline."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RequirementStep(BaseModel):
    action: str
    target: Optional[str] = None
    value: Optional[str] = None
    assertion: Optional[str] = None


class Requirement(BaseModel):
    id: str
    title: str
    description: str
    priority: str = "medium"
    steps: List[RequirementStep] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    source_type: str = "github"  # 'github' | 'document' | 'local'
    origin_id: Optional[str] = None  # issue number, file path, etc.


class TestCaseResult(BaseModel):
    title: str
    status: str
    duration_ms: float = 0
    browser: Optional[str] = None
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    trace_path: Optional[str] = None
    video_path: Optional[str] = None
    console_logs: List[str] = Field(default_factory=list)
    network_errors: List[str] = Field(default_factory=list)
    api_failures: List[str] = Field(default_factory=list)


class RegressionDiff(BaseModel):
    file: str
    status: str  # pass | fail | new_baseline
    diff_percent: float = 0.0
    diff_image_path: Optional[str] = None
    message: Optional[str] = None


class ApiValidationResult(BaseModel):
    url: str
    method: str = "GET"
    expected_status: int = 200
    actual_status: int = 0
    passed: bool = False
    error: Optional[str] = None


class LogIssue(BaseModel):
    test_title: str
    severity: str  # error | warning
    source: str  # console | network
    message: str


class TestResult(BaseModel):
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    total: int = 0
    duration_ms: float = 0
    cases: List[TestCaseResult] = Field(default_factory=list)
    regression_diffs: List[RegressionDiff] = Field(default_factory=list)
    api_validations: List[ApiValidationResult] = Field(default_factory=list)
    log_issues: List[LogIssue] = Field(default_factory=list)
    raw_json: Optional[Dict[str, Any]] = None

    @property
    def all_passed(self) -> bool:
        regression_failed = any(d.status == "fail" for d in self.regression_diffs)
        api_failed = any(not v.passed for v in self.api_validations)
        log_failed = any(i.severity == "error" for i in self.log_issues)
        return (
            self.failed == 0
            and self.total > 0
            and not regression_failed
            and not api_failed
            and not log_failed
        )


class ParsedRequirements(BaseModel):
    source: str
    requirements: List[Requirement] = Field(default_factory=list)


class QualityIssue(BaseModel):
    kind: str  # ambiguous | missing_acceptance_criteria | contradiction | vague_language | untestable
    severity: str = "medium"  # low | medium | high
    message: str


class RequirementQuality(BaseModel):
    requirement_id: str
    score: float  # 0-100
    issues: List[QualityIssue] = Field(default_factory=list)


class ModelDependency(BaseModel):
    """Typed edge between data models (e.g. Order depends_on Payment)."""

    source: str
    target: str
    relation: str = "depends_on"


class RequirementEntities(BaseModel):
    """Data models and business flows a requirement touches -- the grouping
    key behind impact analysis answering "which requirements share a data
    model" / "which automation depends on which flow" (see ROADMAP.md).
    Names are free text (e.g. "Order", "Checkout"), not IDs into any schema
    this repo owns -- grouping is by exact string match. Optional
    model_dependencies capture explicit typed edges named in the requirement
    text (Order depends_on Payment)."""

    requirement_id: str
    data_models: List[str] = Field(default_factory=list)
    flows: List[str] = Field(default_factory=list)
    model_dependencies: List[ModelDependency] = Field(default_factory=list)


class PipelineReport(BaseModel):
    summary: str
    passed: int
    failed: int
    total: int
    failure_analysis: Optional[str] = None
    autofix_suggestions: Optional[List[str]] = None
    html_path: Optional[str] = None
    pdf_path: Optional[str] = None
    coverage_inventory_size: Optional[int] = None
    coverage_gaps_remaining: Optional[int] = None
    coverage_tests_generated: Optional[int] = None
    v8_coverage_percentage: Optional[float] = None


class AutofixSuggestion(BaseModel):
    test_title: str
    original_selector: str
    suggested_selector: str
    confidence: str = "medium"
    explanation: str = ""


class Skill(BaseModel):
    """A confirmed-working autofix fix, remembered for reuse across runs."""

    id: str
    kind: str = "selector_repair"
    original_selector: str
    suggested_selector: str
    test_title: Optional[str] = None
    confidence: str = "medium"
    explanation: str = ""
    times_confirmed: int = 1
    created_run: Optional[str] = None
    last_confirmed_run: Optional[str] = None


class CoverageCandidate(BaseModel):
    id: str
    kind: str  # route | page | doc | api | story
    path: str
    title: str
    signals: List[str] = Field(default_factory=list)
    priority: str = "medium"
    source_file: Optional[str] = None
    context: Optional[str] = None


class CoverageGap(BaseModel):
    candidate: CoverageCandidate
    reason: str = "no matching test found"


class V8CoverageFile(BaseModel):
    url: str
    total_bytes: int = 0
    used_bytes: int = 0
    percentage: float = 0.0


class V8CoverageSummary(BaseModel):
    total_bytes: int = 0
    used_bytes: int = 0
    percentage: float = 0.0
    files: List[V8CoverageFile] = Field(default_factory=list)
