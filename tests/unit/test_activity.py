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

"""Unit tests for orchestrator/dashboard/activity.py's in-memory activity
feeds. Previously only record_job was exercised incidentally elsewhere --
record_webhook, recent, and last_webhook had no direct coverage."""

from __future__ import annotations

import pytest

from orchestrator.dashboard import activity


@pytest.fixture(autouse=True)
def _clean_activity_state():
    activity._jobs.clear()
    activity._webhooks.clear()
    yield
    activity._jobs.clear()
    activity._webhooks.clear()


def test_record_job_truncates_brief_and_rounds_duration():
    activity.record_job("smoke", True, "x" * 200, 1.2345)
    (entry,) = activity._jobs
    assert entry["type"] == "job"
    assert len(entry["brief"]) == 160
    assert entry["duration_s"] == 1.2
    assert entry["ok"] is True


def test_record_webhook_truncates_detail():
    activity.record_webhook("push", "zyvorai/argus", detail="y" * 200)
    (entry,) = activity._webhooks
    assert entry["type"] == "webhook"
    assert entry["event"] == "push"
    assert entry["repo"] == "zyvorai/argus"
    assert len(entry["detail"]) == 120


def test_recent_merges_and_sorts_jobs_and_webhooks_newest_first():
    activity.record_job("smoke", True, "first", 1.0)
    activity.record_webhook("push", "org/repo", detail="second")
    activity.record_job("audit", False, "third", 2.0)

    merged = activity.recent()

    assert [item["brief"] if item["type"] == "job" else item["detail"] for item in merged] == [
        "third",
        "second",
        "first",
    ]


def test_recent_respects_limit():
    for i in range(5):
        activity.record_job("smoke", True, f"job-{i}", 1.0)

    assert len(activity.recent(limit=2)) == 2


def test_last_webhook_returns_none_when_empty():
    assert activity.last_webhook() is None


def test_last_webhook_returns_most_recent():
    activity.record_webhook("push", "org/repo", detail="old")
    activity.record_webhook("pull_request", "org/repo", detail="new")

    assert activity.last_webhook()["detail"] == "new"
