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

"""Unit tests for orchestrator/dashboard/durable_jobs.py.

No real background threads are exercised: `start()`'s thread-spawning is
tested with the loop bodies stubbed out, and `_worker_loop`/
`_scheduler_loop` are called directly (single-threaded, synchronous) with
a mocked store and a mocked `orchestrator.dashboard.jobs` module, driven
to stop after processing exactly one iteration via a `claim_job`/
`due_schedules` side effect that sets the service's own stop event."""

from __future__ import annotations

from unittest.mock import MagicMock

import orchestrator.dashboard.jobs as jobs_module
import orchestrator.dashboard.durable_jobs as durable_jobs
from orchestrator.dashboard.durable_jobs import DurableJobService, _validation_view, get_service


# -- _validation_view ---------------------------------------------------


def test_validation_view_replaces_secret_refs():
    assert _validation_view({"$secret": "env:X"}) == "secret-reference-placeholder"


def test_validation_view_recurses_dict_and_list():
    payload = {"a": [{"$secret": "env:X"}, "plain"], "b": {"c": 1}}
    assert _validation_view(payload) == {
        "a": ["secret-reference-placeholder", "plain"],
        "b": {"c": 1},
    }


def test_validation_view_leaves_plain_values_unchanged():
    assert _validation_view(42) == 42
    assert _validation_view("text") == "text"


# -- DurableJobService.__init__ ------------------------------------------


def test_init_clamps_poll_s_to_minimum():
    service = DurableJobService(store=MagicMock(), poll_s=0.01)
    assert service.poll_s == 0.2


# -- get_service singleton -----------------------------------------------


def test_get_service_returns_singleton(monkeypatch):
    monkeypatch.setattr(durable_jobs, "_service", None)
    first = get_service()
    second = get_service()
    assert first is second


# -- enqueue ---------------------------------------------------------------


def test_enqueue_validates_persists_and_audits(monkeypatch):
    fake_store = MagicMock()
    fake_store.enqueue_job.return_value = {"id": "job-1", "kind": "smoke"}
    service = DurableJobService(store=fake_store)

    fake_validate = MagicMock()
    monkeypatch.setattr(jobs_module, "_validate", fake_validate)

    result = service.enqueue("smoke", {"url": "https://example.org"}, requested_by="alice")

    assert result == {"id": "job-1", "kind": "smoke"}
    fake_validate.assert_called_once_with("smoke", {"url": "https://example.org"})
    fake_store.enqueue_job.assert_called_once()
    fake_store.audit.assert_called_once()
    assert fake_store.audit.call_args.kwargs["resource_id"] == "job-1"


def test_enqueue_substitutes_secret_placeholder_for_validation_only(monkeypatch):
    fake_store = MagicMock()
    fake_store.enqueue_job.return_value = {"id": "job-2", "kind": "audit"}
    service = DurableJobService(store=fake_store)

    fake_validate = MagicMock()
    monkeypatch.setattr(jobs_module, "_validate", fake_validate)

    raw_params = {"token": {"$secret": "env:API_TOKEN"}}
    service.enqueue("audit", raw_params)

    # validation sees the placeholder, not the raw secret reference...
    fake_validate.assert_called_once_with("audit", {"token": "secret-reference-placeholder"})
    # ...but the store persists the real (still-a-reference, never-resolved) params.
    fake_store.enqueue_job.assert_called_once_with(
        "audit", raw_params, requested_by="", idempotency_key=None, priority=100, trace_context=None
    )


# -- start(): recovery + idempotent thread spawn ---------------------------


def test_start_recovers_stale_jobs_and_is_idempotent(monkeypatch):
    fake_store = MagicMock()
    fake_store.recover_stale_jobs.return_value = {"requeued": 2, "dead_lettered": 1}
    service = DurableJobService(store=fake_store)

    fake_inc = MagicMock()
    monkeypatch.setattr(durable_jobs, "inc", fake_inc)
    # Stub the loop bodies so the spawned daemon threads return immediately.
    monkeypatch.setattr(service, "_worker_loop", lambda: None)
    monkeypatch.setattr(service, "_scheduler_loop", lambda: None)

    service.start()
    service.start()  # second call must be a no-op

    fake_store.recover_stale_jobs.assert_called_once()
    fake_inc.assert_any_call("zyvor_qa_jobs_recovered_total", 2)
    fake_inc.assert_any_call("zyvor_qa_jobs_dead_lettered_total", 1)
    assert len(service._threads) == 2
    service.stop()


def test_start_skips_recovery_counters_when_nothing_to_recover(monkeypatch):
    fake_store = MagicMock()
    fake_store.recover_stale_jobs.return_value = {"requeued": 0, "dead_lettered": 0}
    service = DurableJobService(store=fake_store)

    fake_inc = MagicMock()
    monkeypatch.setattr(durable_jobs, "inc", fake_inc)
    monkeypatch.setattr(service, "_worker_loop", lambda: None)
    monkeypatch.setattr(service, "_scheduler_loop", lambda: None)

    service.start()
    fake_inc.assert_not_called()
    service.stop()


# -- _worker_loop ------------------------------------------------------------


class _FakeStopEvent:
    """A synchronous, instant stand-in for threading.Event so `_worker_loop`/
    `_scheduler_loop` can be driven directly in the test thread without any
    real wall-clock waiting between iterations."""

    def __init__(self):
        self._flag = False

    def is_set(self) -> bool:
        return self._flag

    def set(self) -> None:
        self._flag = True

    def wait(self, timeout: float | None = None) -> bool:
        return self._flag


def _service_with_mocks():
    fake_store = MagicMock()
    service = DurableJobService(store=fake_store, poll_s=0.2)
    service._stop = _FakeStopEvent()
    return service, fake_store


def test_worker_loop_completes_a_successful_job(monkeypatch):
    service, fake_store = _service_with_mocks()
    job = {"id": "job-1", "kind": "smoke", "params": {}}

    calls = {"n": 0}

    def fake_claim_job():
        calls["n"] += 1
        if calls["n"] == 1:
            return job
        service._stop.set()
        return None

    fake_store.claim_job.side_effect = fake_claim_job
    fake_store.cancellation_requested.return_value = False

    monkeypatch.setattr(jobs_module, "trigger", lambda kind, params: (True, None))
    monkeypatch.setattr(
        jobs_module, "status", lambda: {"running": False, "error": None, "result": {"ok": True}}
    )

    service._worker_loop()

    fake_store.finish_job.assert_called_once_with("job-1", result={"ok": True}, error=None)
    fake_store.mark_cancelled.assert_not_called()


def test_worker_loop_marks_cancelled_when_user_cancelled(monkeypatch):
    service, fake_store = _service_with_mocks()
    job = {"id": "job-2", "kind": "audit", "params": {}}

    calls = {"n": 0}

    def fake_claim_job():
        calls["n"] += 1
        if calls["n"] == 1:
            return job
        service._stop.set()
        return None

    fake_store.claim_job.side_effect = fake_claim_job
    fake_store.cancellation_requested.return_value = False

    monkeypatch.setattr(jobs_module, "trigger", lambda kind, params: (True, None))
    monkeypatch.setattr(
        jobs_module, "status", lambda: {"running": False, "error": "cancelled by user"}
    )

    service._worker_loop()

    fake_store.mark_cancelled.assert_called_once_with("job-2")
    fake_store.finish_job.assert_not_called()


def test_worker_loop_requeues_when_trigger_reports_busy(monkeypatch):
    service, fake_store = _service_with_mocks()
    job = {"id": "job-3", "kind": "smoke", "params": {}}

    calls = {"n": 0}

    def fake_claim_job():
        calls["n"] += 1
        if calls["n"] == 1:
            return job
        service._stop.set()
        return None

    fake_store.claim_job.side_effect = fake_claim_job
    monkeypatch.setattr(jobs_module, "trigger", lambda kind, params: (False, None))

    service._worker_loop()

    fake_store.requeue_job.assert_called_once_with("job-3", "legacy runner is busy")
    fake_store.finish_job.assert_not_called()


def test_worker_loop_finishes_job_with_error_on_exception(monkeypatch):
    service, fake_store = _service_with_mocks()
    job = {"id": "job-4", "kind": "smoke", "params": {}}

    calls = {"n": 0}

    def fake_claim_job():
        calls["n"] += 1
        if calls["n"] == 1:
            return job
        service._stop.set()
        return None

    fake_store.claim_job.side_effect = fake_claim_job

    def raise_trigger(kind, params):
        raise RuntimeError("legacy runner exploded")

    monkeypatch.setattr(jobs_module, "trigger", raise_trigger)

    service._worker_loop()

    fake_store.finish_job.assert_called_once_with("job-4", error="legacy runner exploded")


def test_worker_loop_cancels_still_running_job_then_finishes_next_poll(monkeypatch):
    """Covers the branch where cancellation is requested while the job is
    still reported as running: jobs.cancel() fires immediately (line 114)
    but the loop keeps polling (line 127) rather than assuming the job
    stopped instantly, and only finishes it once status() actually says so."""
    service, fake_store = _service_with_mocks()
    job = {"id": "job-5", "kind": "smoke", "params": {}}

    claim_calls = {"n": 0}

    def fake_claim_job():
        claim_calls["n"] += 1
        if claim_calls["n"] == 1:
            return job
        service._stop.set()
        return None

    fake_store.claim_job.side_effect = fake_claim_job

    status_calls = {"n": 0}

    def fake_status():
        status_calls["n"] += 1
        if status_calls["n"] == 1:
            return {"running": True}
        return {"running": False, "error": None, "result": {"ok": True}}

    monkeypatch.setattr(jobs_module, "status", fake_status)

    cancel_check_calls = {"n": 0}

    def fake_cancellation_requested(job_id):
        cancel_check_calls["n"] += 1
        return cancel_check_calls["n"] == 1  # only the very first check says "yes"

    fake_store.cancellation_requested.side_effect = fake_cancellation_requested

    fake_cancel = MagicMock()
    monkeypatch.setattr(jobs_module, "cancel", fake_cancel)
    monkeypatch.setattr(jobs_module, "trigger", lambda kind, params: (True, None))

    service._worker_loop()

    fake_cancel.assert_called_once()
    fake_store.finish_job.assert_called_once_with("job-5", result={"ok": True}, error=None)


def test_worker_loop_idles_when_no_job_is_claimable(monkeypatch):
    service, fake_store = _service_with_mocks()

    calls = {"n": 0}

    def fake_claim_job():
        calls["n"] += 1
        if calls["n"] >= 2:
            service._stop.set()
        return None

    fake_store.claim_job.side_effect = fake_claim_job

    service._worker_loop()

    assert calls["n"] >= 2
    fake_store.finish_job.assert_not_called()


# -- _scheduler_loop -----------------------------------------------------------


def test_scheduler_loop_enqueues_due_schedule_and_advances(monkeypatch):
    service, fake_store = _service_with_mocks()
    schedule = {"id": "sched-1", "kind": "smoke", "params": {}, "requested_by": "", "runs": 3}

    calls = {"n": 0}

    def fake_due_schedules():
        calls["n"] += 1
        if calls["n"] == 1:
            return [schedule]
        service._stop.set()
        return []

    fake_store.due_schedules.side_effect = fake_due_schedules
    fake_store.enqueue_job.return_value = {"id": "job-x"}
    monkeypatch.setattr(jobs_module, "_validate", MagicMock())

    service._scheduler_loop()

    fake_store.advance_schedule.assert_called_once_with("sched-1", ran=True)
    assert fake_store.enqueue_job.call_args.kwargs["idempotency_key"] == "schedule:sched-1:4"


def test_scheduler_loop_records_failure_when_enqueue_raises(monkeypatch):
    service, fake_store = _service_with_mocks()
    schedule = {"id": "sched-2", "kind": "smoke", "params": {}, "requested_by": "", "runs": 0}

    calls = {"n": 0}

    def fake_due_schedules():
        calls["n"] += 1
        if calls["n"] == 1:
            return [schedule]
        service._stop.set()
        return []

    fake_store.due_schedules.side_effect = fake_due_schedules

    def raise_validate(kind, params):
        raise RuntimeError("bad params")

    monkeypatch.setattr(jobs_module, "_validate", raise_validate)

    service._scheduler_loop()

    fake_store.advance_schedule.assert_called_once_with("sched-2", ran=False)
    fake_store.audit.assert_called_once()
    assert fake_store.audit.call_args.kwargs["outcome"] == "failure"
