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

"""Deterministic resilience-assessment rubric for `chaos_inject`/
`chaos_webhook` -- no LLM call, unlike exploit_poc's script-generation path.
There's no ambiguity to resolve here: "did the target degrade gracefully
under fault" reduces to three measurable signals (see ROADMAP.md's
chaos-testing section for the full design rationale):

1. No raw stack trace / unstructured error leaked to the client.
2. Error rate during the fault window stayed under an operator-set threshold.
3. Latency recovered to baseline within an operator-set SLA after the fault
   was removed.
"""

from __future__ import annotations

_STACK_TRACE_MARKERS = (
    "Traceback (most recent call last)",
    '  File "',
    "at java.",
    "Exception in thread",
    "NullPointerException",
    "panic:",
    "node_modules/",
    "    at Object.",
    "Fatal error:",
    "Unhandled exception",
    "django.core.exceptions",
    "System.Exception",
)


def looks_like_stack_trace(text: str) -> bool:
    """Heuristic-only: looks for common stack-trace/unstructured-error
    markers across a handful of languages/runtimes. A false negative
    doesn't mean the error response was actually clean -- this is a
    pragmatic signal, not a guarantee, same posture as
    agents/probes/misconfig_scan.py's check_consent_signals()."""
    return any(marker in text for marker in _STACK_TRACE_MARKERS)


def assess_resilience(
    *,
    error_rate_pct: float,
    error_rate_threshold_pct: float,
    recovery_s: float | None,
    recovery_sla_s: float,
    error_bodies: list[str] | None = None,
) -> tuple[bool, str]:
    """Returns `(graceful, reason)`. `reason` always names every violated
    criterion (joined, not just the first) so a `medium`/`high` finding's
    detail is immediately actionable rather than requiring a re-run to see
    what else failed."""
    reasons: list[str] = []

    leaked = [body for body in (error_bodies or []) if looks_like_stack_trace(body)]
    if leaked:
        reasons.append(
            f"{len(leaked)} error response(s) leaked a raw stack trace/unstructured error instead of a clean one"
        )

    if error_rate_pct > error_rate_threshold_pct:
        reasons.append(f"error rate {error_rate_pct:.1f}% exceeded the {error_rate_threshold_pct:.1f}% threshold")

    if recovery_s is None:
        reasons.append(f"target did not recover to baseline latency within the {recovery_sla_s:.1f}s observation window")
    elif recovery_s > recovery_sla_s:
        reasons.append(f"recovery took {recovery_s:.1f}s, exceeding the {recovery_sla_s:.1f}s SLA")

    if reasons:
        return False, "; ".join(reasons)
    return True, "error rate and recovery time within bounds, no raw stack traces leaked"
