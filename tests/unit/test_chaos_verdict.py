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

"""Unit tests for agents/chaos/verdict.py -- the deterministic resilience
rubric shared by chaos_inject/chaos_webhook."""

from __future__ import annotations

from agents.chaos.verdict import assess_resilience, looks_like_stack_trace


def test_graceful_when_all_three_criteria_met():
    ok, reason = assess_resilience(
        error_rate_pct=2.0, error_rate_threshold_pct=5.0, recovery_s=3.0, recovery_sla_s=10.0,
    )
    assert ok is True
    assert "within bounds" in reason


def test_ungraceful_when_error_rate_exceeds_threshold():
    ok, reason = assess_resilience(
        error_rate_pct=50.0, error_rate_threshold_pct=5.0, recovery_s=3.0, recovery_sla_s=10.0,
    )
    assert ok is False
    assert "error rate" in reason


def test_ungraceful_when_recovery_exceeds_sla():
    ok, reason = assess_resilience(
        error_rate_pct=0.0, error_rate_threshold_pct=5.0, recovery_s=20.0, recovery_sla_s=10.0,
    )
    assert ok is False
    assert "recovery took" in reason


def test_ungraceful_when_never_recovers():
    ok, reason = assess_resilience(
        error_rate_pct=0.0, error_rate_threshold_pct=5.0, recovery_s=None, recovery_sla_s=10.0,
    )
    assert ok is False
    assert "did not recover" in reason


def test_ungraceful_when_stack_trace_leaked():
    ok, reason = assess_resilience(
        error_rate_pct=0.0, error_rate_threshold_pct=5.0, recovery_s=1.0, recovery_sla_s=10.0,
        error_bodies=["Traceback (most recent call last):\n  File \"app.py\", line 1"],
    )
    assert ok is False
    assert "stack trace" in reason


def test_clean_json_error_body_is_not_flagged_as_a_stack_trace():
    ok, _ = assess_resilience(
        error_rate_pct=0.0, error_rate_threshold_pct=5.0, recovery_s=1.0, recovery_sla_s=10.0,
        error_bodies=['{"error": "service temporarily unavailable"}'],
    )
    assert ok is True


def test_multiple_violations_are_all_named_not_just_the_first():
    ok, reason = assess_resilience(
        error_rate_pct=99.0, error_rate_threshold_pct=5.0, recovery_s=None, recovery_sla_s=10.0,
        error_bodies=["panic: runtime error"],
    )
    assert ok is False
    assert "error rate" in reason
    assert "did not recover" in reason
    assert "stack trace" in reason


def test_looks_like_stack_trace_python():
    assert looks_like_stack_trace('Traceback (most recent call last):\n  File "x.py", line 1, in <module>')


def test_looks_like_stack_trace_java():
    assert looks_like_stack_trace("Exception in thread \"main\" java.lang.NullPointerException\n\tat java.base/Foo.bar")


def test_looks_like_stack_trace_node():
    assert looks_like_stack_trace("TypeError: Cannot read property 'x'\n    at Object.<anonymous> (/app/node_modules/foo.js:1:1)")


def test_looks_like_stack_trace_false_for_structured_error():
    assert not looks_like_stack_trace('{"error": "not found", "code": 404}')


def test_looks_like_stack_trace_false_for_plain_html():
    assert not looks_like_stack_trace("<html><body><h1>503 Service Unavailable</h1></body></html>")
