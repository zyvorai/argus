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

"""Latency/recovery measurement shared by `chaos_inject` and
`chaos_webhook` -- plain HTTP timing against the target, no privileged
operations, so unlike the fault-injection mechanism itself this is fully
testable outside a sandbox."""

from __future__ import annotations

import time


def measure_latency_s(url: str, *, insecure: bool = False, timeout_s: float = 10) -> float | None:
    """One GET, wall-clock timed. None on any request failure (connection
    refused, timeout, ...) -- a failed request isn't "zero latency", it's
    an unmeasurable one, and callers must not conflate the two."""
    import httpx

    start = time.monotonic()
    try:
        with httpx.Client(verify=not insecure, timeout=timeout_s) as client:
            client.get(url)
    except Exception:
        return None
    return time.monotonic() - start


def measure_recovery_s(
    url: str,
    baseline_s: float,
    *,
    tolerance_factor: float = 1.5,
    max_wait_s: float,
    poll_interval_s: float = 1.0,
    insecure: bool = False,
) -> float | None:
    """Polls `url` until latency drops back to within `tolerance_factor`x
    the pre-fault baseline, or `max_wait_s` elapses. Returns seconds elapsed
    until recovery, or None if it never recovered within the window --
    None is a real, distinct outcome (assess_resilience treats it as a
    resilience gap), not an error."""
    threshold = baseline_s * tolerance_factor
    start = time.monotonic()
    deadline = start + max_wait_s
    while time.monotonic() < deadline:
        latency = measure_latency_s(url, insecure=insecure, timeout_s=max(1.0, threshold))
        if latency is not None and latency <= threshold:
            return time.monotonic() - start
        time.sleep(poll_interval_s)
    return None
