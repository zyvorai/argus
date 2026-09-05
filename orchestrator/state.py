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

"""Pipeline state shared across LangGraph nodes."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

from agents.common.models import (
    ApiValidationResult,
    AutofixSuggestion,
    CoverageCandidate,
    CoverageGap,
    LogIssue,
    RegressionDiff,
    Requirement,
    TestResult,
    V8CoverageSummary,
)


class PipelineState(TypedDict, total=False):
    source: str
    spec_paths: List[str]
    spec_contents: List[str]
    document_paths: List[str]
    jira_issue_keys: List[str]
    requirements: List[Requirement]
    requirement_quality: Dict[str, Any]
    requirement_impact: Dict[str, List[str]]
    generated_tests: List[str]
    test_results: Optional[TestResult]
    regression_diffs: List[RegressionDiff]
    api_validations: List[ApiValidationResult]
    log_issues: List[LogIssue]
    failure_analysis: Optional[str]
    autofix_suggestions: List[AutofixSuggestion]
    report_path: Optional[str]
    pdf_report_path: Optional[str]
    report_summary: Optional[str]
    pr_number: Optional[int]
    repo_full_name: Optional[str]
    error: Optional[str]
    metadata: Dict[str, Any]
    expand_coverage: bool
    coverage_inventory: List[CoverageCandidate]
    coverage_gaps: List[CoverageGap]
    v8_coverage: Optional[V8CoverageSummary]
