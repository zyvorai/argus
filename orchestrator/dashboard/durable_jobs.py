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

"""Durable Mission Control job and schedule service.

It wraps the existing `orchestrator.dashboard.jobs` execution functions, while
persisting queue state and schedules in SQLite. The interface can later be moved
to PostgreSQL/Temporal without changing `/api/v2`.
"""

from __future__ import annotations

import os
import threading
import time
from typing import Any

from orchestrator.observability.metrics import inc, set_gauge
from orchestrator.observability.tracing import current_traceparent, set_span_error, start_span
from orchestrator.persistence.store import MissionControlStore, get_store
from orchestrator.security.secrets import is_secret_ref, resolve_secret_refs


class DurableJobService:
    def __init__(self, store: MissionControlStore | None = None, *, poll_s: float = 1.0) -> None:
        self.store = store or get_store()
        self.poll_s = max(0.2, poll_s)
        self._stop = threading.Event()
        self._threads: list[threading.Thread] = []
        self._started = False
        self._start_lock = threading.Lock()

    def start(self) -> None:
        with self._start_lock:
            if self._started:
                return
            self._started = True
            recovery = self.store.recover_stale_jobs()
            if recovery["requeued"]:
                inc("zyvor_qa_jobs_recovered_total", recovery["requeued"])
            if recovery["dead_lettered"]:
                inc("zyvor_qa_jobs_dead_lettered_total", recovery["dead_lettered"])
            for name, target in (("zyvor-job-worker", self._worker_loop), ("zyvor-scheduler", self._scheduler_loop)):
                thread = threading.Thread(target=target, name=name, daemon=True)
                thread.start()
                self._threads.append(thread)

    def stop(self) -> None:
        self._stop.set()
        for thread in self._threads:
            thread.join(timeout=3)

    def enqueue(
        self,
        kind: str,
        params: dict[str, Any],
        *,
        requested_by: str = "",
        idempotency_key: str | None = None,
        priority: int = 100,
    ) -> dict[str, Any]:
        from orchestrator.dashboard import jobs

        # Validate shape immediately, substituting harmless placeholders for refs.
        jobs._validate(kind, _validation_view(params))
        with start_span("job.enqueue", job_kind=kind) as span:
            trace_context = current_traceparent() if span else None
            job = self.store.enqueue_job(
                kind,
                params,
                requested_by=requested_by,
                idempotency_key=idempotency_key,
                priority=priority,
                trace_context=trace_context,
            )
            if span:
                span.set_attribute("job.id", job["id"])
        self.store.audit(
            "job.enqueue", actor=requested_by, resource_type="job", resource_id=job["id"],
            detail={"kind": kind, "params": params},
        )
        inc("zyvor_qa_jobs_enqueued_total", kind=kind)
        return job

    def _worker_loop(self) -> None:
        from orchestrator.dashboard import jobs

        while not self._stop.is_set():
            job = self.store.claim_job()
            if not job:
                set_gauge("zyvor_qa_worker_busy", 0)
                self._stop.wait(self.poll_s)
                continue
            set_gauge("zyvor_qa_worker_busy", 1)
            job_id = job["id"]
            kind = job["kind"]
            started_at = time.monotonic()
            with start_span(
                "job.execute", trace_context=job.get("trace_context"), job_id=job_id, job_kind=kind
            ) as span:
                try:
                    params = resolve_secret_refs(job["params"])
                    started, _ = jobs.trigger(kind, params)
                    if not started:
                        self.store.requeue_job(job_id, "legacy runner is busy")
                        if span:
                            span.set_attribute("job.status", "requeued")
                        self._stop.wait(self.poll_s)
                        continue

                    while not self._stop.is_set():
                        self.store.heartbeat(job_id)
                        state = jobs.status()
                        if self.store.cancellation_requested(job_id):
                            jobs.cancel()
                        if not state.get("running"):
                            error = state.get("error")
                            if error == "cancelled by user" or self.store.cancellation_requested(job_id):
                                self.store.mark_cancelled(job_id)
                                inc("zyvor_qa_jobs_completed_total", kind=kind, status="cancelled")
                                if span:
                                    span.set_attribute("job.status", "cancelled")
                            else:
                                self.store.finish_job(job_id, result=state.get("result"), error=error)
                                status = "failed" if error else "succeeded"
                                inc("zyvor_qa_jobs_completed_total", kind=kind, status=status)
                                if span:
                                    span.set_attribute("job.status", status)
                                if error:
                                    set_span_error(span, error)
                            break
                        self._stop.wait(self.poll_s)
                except Exception as exc:
                    self.store.finish_job(job_id, error=str(exc)[:2000])
                    inc("zyvor_qa_jobs_completed_total", kind=kind, status="failed")
                    set_span_error(span, str(exc))
                finally:
                    duration = time.monotonic() - started_at
                    set_gauge("zyvor_qa_last_job_duration_seconds", duration, kind=kind)
                    set_gauge("zyvor_qa_worker_busy", 0)
                    if span:
                        span.set_attribute("job.duration_s", round(duration, 3))

    def _scheduler_loop(self) -> None:
        while not self._stop.is_set():
            due = self.store.due_schedules()
            set_gauge("zyvor_qa_schedules_due", len(due))
            skip_if_busy = os.environ.get("ZYVOR_SCHEDULE_SKIP_IF_BUSY", "false").lower() in {
                "1",
                "true",
                "yes",
                "on",
            }
            for schedule in due:
                try:
                    if skip_if_busy:
                        from orchestrator.dashboard import jobs as jobs_mod

                        if jobs_mod.status().get("running"):
                            # Preserve due time until the runner is free (do not advance).
                            continue
                    self.enqueue(
                        schedule["kind"],
                        schedule["params"],
                        requested_by=schedule.get("requested_by") or "scheduler",
                        idempotency_key=f"schedule:{schedule['id']}:{schedule['runs'] + 1}",
                    )
                    self.store.advance_schedule(schedule["id"], ran=True)
                    inc("zyvor_qa_schedule_runs_total", kind=schedule["kind"], status="queued")
                except Exception as exc:
                    self.store.advance_schedule(schedule["id"], ran=False)
                    self.store.audit(
                        "schedule.enqueue", actor="scheduler", resource_type="schedule",
                        resource_id=schedule["id"], outcome="failure", detail={"error": str(exc)},
                    )
                    inc("zyvor_qa_schedule_runs_total", kind=schedule["kind"], status="failed")
            self._stop.wait(5)


def _validation_view(value: Any) -> Any:
    if is_secret_ref(value):
        return "secret-reference-placeholder"
    if isinstance(value, dict):
        return {k: _validation_view(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_validation_view(v) for v in value]
    return value


_service: DurableJobService | None = None
_service_lock = threading.Lock()


def get_service() -> DurableJobService:
    global _service
    with _service_lock:
        if _service is None:
            _service = DurableJobService()
        return _service
