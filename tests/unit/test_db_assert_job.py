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

"""Unit tests for orchestrator/dashboard/jobs.py's _job_db_assert -- in
particular, that the resolved db_secret VALUE never leaks into audit logs,
findings, or the returned result payload (mirrors
tests/unit/test_pentest_jobs.py's shape for host_pentest/cloud_pentest),
while the query/assertion text -- not secret -- IS expected to appear in
the audit trail, since db_assert's "code" is a fixed script, not something
generated per run; the query+assertion are the auditable artifact."""

from __future__ import annotations

import os

import pytest

import orchestrator.dashboard.findings as findings_module
import orchestrator.dashboard.history as history_module
import orchestrator.dashboard.jobs as jobs_module
import orchestrator.persistence.store as store_module
import orchestrator.security.sandbox as sandbox_module


class _RecordingStore:
    def __init__(self):
        self.audit_calls = []

    def audit(self, *a, **kw):
        self.audit_calls.append((a, kw))


def _patch_common(monkeypatch, store):
    monkeypatch.setattr(history_module, "append_run", lambda *a, **kw: None)
    monkeypatch.setattr(store_module, "get_store", lambda: store)
    monkeypatch.setattr(sandbox_module, "available", lambda: True)


def _base_params(**overrides):
    params = {
        "engine": "postgres", "target": "staging-orders-db",
        "db_secret": {"$secret": "env:ZYVOR_TEST_DB_SECRET"},
        "query": "SELECT * FROM orders WHERE id = %s", "query_params": [1],
        "assertion": {"mode": "row_count", "op": "==", "value": 1}, "timeout_s": 30,
    }
    params.update(overrides)
    return params


def test_raises_without_sandbox_available(monkeypatch):
    store = _RecordingStore()
    _patch_common(monkeypatch, store)
    monkeypatch.setattr(sandbox_module, "available", lambda: False)

    with pytest.raises(RuntimeError, match="sandbox unavailable"):
        jobs_module._job_db_assert(_base_params())


def test_raises_without_db_image_configured(monkeypatch):
    store = _RecordingStore()
    _patch_common(monkeypatch, store)
    monkeypatch.setattr(sandbox_module, "db_image", lambda: None)

    with pytest.raises(RuntimeError, match="ZYVOR_SANDBOX_DB_IMAGE"):
        jobs_module._job_db_assert(_base_params())


def test_never_leaks_resolved_secret_value_but_does_reach_sandbox_env(monkeypatch):
    store = _RecordingStore()
    _patch_common(monkeypatch, store)
    monkeypatch.setattr(sandbox_module, "db_image", lambda: "custom/db-image:latest")

    secret_value = "postgresql://user:S3cr3tP@ssw0rd!!@db.internal/orders"
    os.environ["ZYVOR_TEST_DB_SECRET"] = secret_value

    captured_run_kwargs = {}

    def fake_run_python(code, **kw):
        captured_run_kwargs["code"] = code
        captured_run_kwargs.update(kw)
        return sandbox_module.SandboxResult(
            exit_code=0, stdout="VERIFIED: true - row_count 1 satisfies == 1\nROW_COUNT: 1\n",
            timed_out=False, network_policy_applied=False,
        )

    monkeypatch.setattr(sandbox_module, "run_python", fake_run_python)
    monkeypatch.setattr(findings_module, "add", lambda *a, **kw: None)

    result = jobs_module._job_db_assert(_base_params())

    assert secret_value not in str(result)
    for call_args, call_kwargs in store.audit_calls:
        assert secret_value not in str(call_args)
        assert secret_value not in str(call_kwargs)
    # but it DOES reach the sandbox execution env -- that's the whole point.
    assert captured_run_kwargs["env"]["ZYVOR_DB_SECRET"] == secret_value
    assert captured_run_kwargs["image"] == "custom/db-image:latest"
    assert result["passed"] is True


def test_query_and_assertion_are_not_secret_and_appear_in_audit(monkeypatch):
    """Unlike host_pentest/cloud_pentest's LLM-generated code (hashed and
    audited by hash only), db_assert's script is fixed -- the query and
    assertion ARE the auditable per-run artifact, so they should appear in
    the audit detail in full."""
    store = _RecordingStore()
    _patch_common(monkeypatch, store)
    monkeypatch.setattr(sandbox_module, "db_image", lambda: "custom/db-image:latest")
    os.environ["ZYVOR_TEST_DB_SECRET2"] = "postgresql://x"
    monkeypatch.setattr(
        sandbox_module, "run_python",
        lambda code, **kw: sandbox_module.SandboxResult(
            exit_code=0, stdout="VERIFIED: true - ok\nROW_COUNT: 1\n", timed_out=False, network_policy_applied=False,
        ),
    )
    monkeypatch.setattr(findings_module, "add", lambda *a, **kw: None)

    jobs_module._job_db_assert(_base_params(db_secret={"$secret": "env:ZYVOR_TEST_DB_SECRET2"}))

    run_calls = [c for c in store.audit_calls if c[0][0] == "db_assert.run"]
    assert len(run_calls) == 1
    detail = run_calls[0][1]["detail"]
    assert detail["query"] == "SELECT * FROM orders WHERE id = %s"
    assert detail["target"] == "staging-orders-db"


def test_records_medium_finding_when_assertion_fails(monkeypatch):
    store = _RecordingStore()
    _patch_common(monkeypatch, store)
    monkeypatch.setattr(sandbox_module, "db_image", lambda: "custom/db-image:latest")
    os.environ["ZYVOR_TEST_DB_SECRET3"] = "postgresql://x"
    monkeypatch.setattr(
        sandbox_module, "run_python",
        lambda code, **kw: sandbox_module.SandboxResult(
            exit_code=0, stdout="VERIFIED: false - row_count 0 does not satisfy == 1\nROW_COUNT: 0\n",
            timed_out=False, network_policy_applied=False,
        ),
    )
    recorded = []
    monkeypatch.setattr(findings_module, "add", lambda *a, **kw: recorded.append(a))

    result = jobs_module._job_db_assert(_base_params(db_secret={"$secret": "env:ZYVOR_TEST_DB_SECRET3"}))

    assert result["passed"] is False
    assert len(recorded) == 1
    assert recorded[0][0] == "db_assert"
    assert recorded[0][1] == "medium"  # a test failure, never critical/high like the pentest kinds
    assert len(result["findings"]) == 1


def test_no_finding_recorded_when_assertion_passes(monkeypatch):
    store = _RecordingStore()
    _patch_common(monkeypatch, store)
    monkeypatch.setattr(sandbox_module, "db_image", lambda: "custom/db-image:latest")
    os.environ["ZYVOR_TEST_DB_SECRET4"] = "postgresql://x"
    monkeypatch.setattr(
        sandbox_module, "run_python",
        lambda code, **kw: sandbox_module.SandboxResult(
            exit_code=0, stdout="VERIFIED: true - ok\nROW_COUNT: 1\n", timed_out=False, network_policy_applied=False,
        ),
    )
    recorded = []
    monkeypatch.setattr(findings_module, "add", lambda *a, **kw: recorded.append(a))

    result = jobs_module._job_db_assert(_base_params(db_secret={"$secret": "env:ZYVOR_TEST_DB_SECRET4"}))

    assert result["passed"] is True
    assert recorded == []
    assert result["findings"] == []


def test_dispatch_table_registration():
    assert jobs_module._JOBS["db_assert"] is jobs_module._job_db_assert
    assert "db_assert" in jobs_module.VALID_KINDS
    assert jobs_module.ELEVATED_RISK_KINDS["db_assert"] == "active_recon"
