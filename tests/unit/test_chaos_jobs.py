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

"""Unit tests for orchestrator/dashboard/jobs.py's _job_chaos_inject and
_job_chaos_webhook, with sandbox/control-test execution mocked (the deeper
mechanics -- agents/chaos/probe.py, verdict.py, inject_script.py -- have
their own dedicated tests with real subprocesses/real HTTP servers; see
those files' test modules). Mirrors test_db_assert_job.py's shape."""

from __future__ import annotations

import httpx
import pytest

import orchestrator.dashboard.findings as findings_module
import orchestrator.dashboard.history as history_module
import orchestrator.dashboard.jobs as jobs_module
import orchestrator.security.sandbox as sandbox_module

_RealHttpxClient = httpx.Client


def _patch_common(monkeypatch):
    monkeypatch.setattr(history_module, "append_run", lambda *a, **kw: None)


def _base_inject_params(**overrides):
    params = {
        "url": "http://target.example.com/", "fault_type": "latency",
        "latency_ms": 200, "packet_loss_pct": 0, "duration_s": 10,
        "control_kind": "flow", "control_params": {"url": "http://target.example.com/"},
        "error_rate_threshold_pct": 10.0, "recovery_sla_s": 10.0, "insecure": False,
    }
    params.update(overrides)
    return params


def _base_webhook_params(**overrides):
    params = {
        "url": "http://target.example.com/", "experiment_webhook_url": "http://chaos.example.com/start",
        "experiment_stop_webhook_url": "http://chaos.example.com/stop", "settle_s": 1,
        "control_kind": "flow", "control_params": {"url": "http://target.example.com/"},
        "error_rate_threshold_pct": 10.0, "recovery_sla_s": 10.0, "insecure": False,
    }
    params.update(overrides)
    return params


# -- chaos_inject ------------------------------------------------------------

def test_chaos_inject_raises_without_sandbox_available(monkeypatch):
    _patch_common(monkeypatch)
    monkeypatch.setattr(sandbox_module, "available", lambda: False)
    with pytest.raises(RuntimeError, match="sandbox unavailable"):
        jobs_module._job_chaos_inject(_base_inject_params())


def test_chaos_inject_raises_without_chaos_image_configured(monkeypatch):
    _patch_common(monkeypatch)
    monkeypatch.setattr(sandbox_module, "available", lambda: True)
    monkeypatch.setattr(sandbox_module, "chaos_image", lambda: None)
    with pytest.raises(RuntimeError, match="ZYVOR_SANDBOX_CHAOS_IMAGE"):
        jobs_module._job_chaos_inject(_base_inject_params())


def test_chaos_inject_graceful_when_control_test_passes_and_recovers(monkeypatch):
    _patch_common(monkeypatch)
    monkeypatch.setattr(sandbox_module, "available", lambda: True)
    monkeypatch.setattr(sandbox_module, "chaos_image", lambda: "custom/chaos-image:latest")
    monkeypatch.setattr(sandbox_module, "run_chaos", lambda code, **kw: sandbox_module.SandboxResult(
        exit_code=0, stdout='RESULT: {"phase": "teardown_complete"}\n', timed_out=False, network_policy_applied=True,
    ))
    monkeypatch.setattr(jobs_module, "_JOBS", {
        **jobs_module._JOBS,
        "flow": lambda params: {"passed": 3, "failed": 0, "total": 3, "flow_steps": []},
    })
    monkeypatch.setattr("agents.chaos.probe.measure_latency_s", lambda *a, **kw: 0.05)
    monkeypatch.setattr("agents.chaos.probe.measure_recovery_s", lambda *a, **kw: 1.0)
    recorded = []
    monkeypatch.setattr(findings_module, "add", lambda *a, **kw: recorded.append(a))

    result = jobs_module._job_chaos_inject(_base_inject_params())

    assert result["graceful"] is True
    assert result["control_kind"] == "flow"
    assert result["network_policy_applied"] is True
    assert recorded == []
    assert result["findings"] == []


def test_chaos_inject_records_finding_on_resilience_gap(monkeypatch):
    _patch_common(monkeypatch)
    monkeypatch.setattr(sandbox_module, "available", lambda: True)
    monkeypatch.setattr(sandbox_module, "chaos_image", lambda: "custom/chaos-image:latest")
    monkeypatch.setattr(sandbox_module, "run_chaos", lambda code, **kw: sandbox_module.SandboxResult(
        exit_code=0, stdout="", timed_out=False, network_policy_applied=False,
    ))
    monkeypatch.setattr(jobs_module, "_JOBS", {
        **jobs_module._JOBS,
        "flow": lambda params: {"passed": 0, "failed": 3, "total": 3, "flow_steps": []},
    })
    monkeypatch.setattr("agents.chaos.probe.measure_latency_s", lambda *a, **kw: 0.05)
    monkeypatch.setattr("agents.chaos.probe.measure_recovery_s", lambda *a, **kw: None)
    recorded = []
    monkeypatch.setattr(findings_module, "add", lambda *a, **kw: recorded.append(a))

    result = jobs_module._job_chaos_inject(_base_inject_params())

    assert result["graceful"] is False
    assert len(recorded) == 1
    assert recorded[0][0] == "chaos_inject"
    assert recorded[0][1] == "high"  # recovery_s is None -> high, not medium
    assert len(result["findings"]) == 1


def test_chaos_inject_calls_control_kind_with_its_own_params(monkeypatch):
    """Confirms the concurrent control test really is invoked with the
    validated control_params, not silently dropped."""
    _patch_common(monkeypatch)
    monkeypatch.setattr(sandbox_module, "available", lambda: True)
    monkeypatch.setattr(sandbox_module, "chaos_image", lambda: "custom/chaos-image:latest")
    monkeypatch.setattr(sandbox_module, "run_chaos", lambda code, **kw: sandbox_module.SandboxResult(
        exit_code=0, stdout="", timed_out=False, network_policy_applied=False,
    ))
    captured = {}

    def fake_flow(params):
        captured.update(params)
        return {"passed": 1, "failed": 0, "total": 1, "flow_steps": []}

    monkeypatch.setattr(jobs_module, "_JOBS", {**jobs_module._JOBS, "flow": fake_flow})
    monkeypatch.setattr("agents.chaos.probe.measure_latency_s", lambda *a, **kw: 0.05)
    monkeypatch.setattr("agents.chaos.probe.measure_recovery_s", lambda *a, **kw: 1.0)
    monkeypatch.setattr(findings_module, "add", lambda *a, **kw: None)

    jobs_module._job_chaos_inject(_base_inject_params(control_params={"url": "http://target.example.com/", "description": "x"}))

    assert captured["description"] == "x"


# -- chaos_webhook -------------------------------------------------------------

def test_chaos_webhook_triggers_and_stops_experiment(monkeypatch):
    _patch_common(monkeypatch)
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(200)

    monkeypatch.setattr(httpx, "Client", lambda **kw: _RealHttpxClient(transport=httpx.MockTransport(handler)))
    monkeypatch.setattr(jobs_module, "_JOBS", {
        **jobs_module._JOBS,
        "flow": lambda params: {"passed": 1, "failed": 0, "total": 1, "flow_steps": []},
    })
    monkeypatch.setattr("agents.chaos.probe.measure_latency_s", lambda *a, **kw: 0.05)
    monkeypatch.setattr("agents.chaos.probe.measure_recovery_s", lambda *a, **kw: 1.0)
    monkeypatch.setattr(findings_module, "add", lambda *a, **kw: None)
    import time as time_module
    monkeypatch.setattr(time_module, "sleep", lambda s: None)

    result = jobs_module._job_chaos_webhook(_base_webhook_params(settle_s=1))

    assert "http://chaos.example.com/start" in calls
    assert "http://chaos.example.com/stop" in calls
    assert result["graceful"] is True


def test_chaos_webhook_skips_stop_call_when_not_configured(monkeypatch):
    _patch_common(monkeypatch)
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(200)

    monkeypatch.setattr(httpx, "Client", lambda **kw: _RealHttpxClient(transport=httpx.MockTransport(handler)))
    monkeypatch.setattr(jobs_module, "_JOBS", {
        **jobs_module._JOBS,
        "flow": lambda params: {"passed": 1, "failed": 0, "total": 1, "flow_steps": []},
    })
    monkeypatch.setattr("agents.chaos.probe.measure_latency_s", lambda *a, **kw: 0.05)
    monkeypatch.setattr("agents.chaos.probe.measure_recovery_s", lambda *a, **kw: 1.0)
    monkeypatch.setattr(findings_module, "add", lambda *a, **kw: None)
    import time as time_module
    monkeypatch.setattr(time_module, "sleep", lambda s: None)

    jobs_module._job_chaos_webhook(_base_webhook_params(experiment_stop_webhook_url=""))

    assert calls == ["http://chaos.example.com/start"]


def test_chaos_webhook_stop_call_failure_is_non_fatal(monkeypatch):
    _patch_common(monkeypatch)

    def handler(request: httpx.Request) -> httpx.Response:
        if "stop" in str(request.url):
            raise httpx.ConnectError("refused", request=request)
        return httpx.Response(200)

    monkeypatch.setattr(httpx, "Client", lambda **kw: _RealHttpxClient(transport=httpx.MockTransport(handler)))
    monkeypatch.setattr(jobs_module, "_JOBS", {
        **jobs_module._JOBS,
        "flow": lambda params: {"passed": 1, "failed": 0, "total": 1, "flow_steps": []},
    })
    monkeypatch.setattr("agents.chaos.probe.measure_latency_s", lambda *a, **kw: 0.05)
    monkeypatch.setattr("agents.chaos.probe.measure_recovery_s", lambda *a, **kw: 1.0)
    monkeypatch.setattr(findings_module, "add", lambda *a, **kw: None)
    import time as time_module
    monkeypatch.setattr(time_module, "sleep", lambda s: None)

    # must not raise even though the stop-webhook call fails
    result = jobs_module._job_chaos_webhook(_base_webhook_params())
    assert result["graceful"] is True


def test_dispatch_and_registration():
    assert jobs_module._JOBS["chaos_inject"] is jobs_module._job_chaos_inject
    assert jobs_module._JOBS["chaos_webhook"] is jobs_module._job_chaos_webhook
    assert "chaos_inject" in jobs_module.VALID_KINDS
    assert "chaos_webhook" in jobs_module.VALID_KINDS
    assert jobs_module.ELEVATED_RISK_KINDS["chaos_inject"] == "exploit"
    assert jobs_module.ELEVATED_RISK_KINDS["chaos_webhook"] == "exploit"
