# Copyright 2026 Zyvor AI Labs · https://zyvor.dev
# SPDX-License-Identifier: LicenseRef-Zyvor-Production-1.0
from __future__ import annotations

import orchestrator.dashboard.durable_jobs as durable_jobs
import orchestrator.persistence.store as persistence_store
from orchestrator.slack_gateway import handle_slash_command


class _FakeService:
    def __init__(self, job):
        self._job = job
        self.calls = []

    def enqueue(self, kind, params, *, requested_by=""):
        self.calls.append((kind, params, requested_by))
        return self._job


class _FakeStore:
    def __init__(self, job=None):
        self._job = job

    def get_job(self, job_id):
        return self._job if self._job and self._job["id"] == job_id else None


def test_run_enqueues_supported_kind(monkeypatch):
    fake_service = _FakeService({"id": "job-123", "kind": "smoke", "status": "queued"})
    monkeypatch.setattr(durable_jobs, "get_service", lambda: fake_service)

    reply = handle_slash_command("run smoke", requested_by="slack:alice")

    assert reply["response_type"] == "in_channel"
    assert "job-123" in reply["text"]
    assert fake_service.calls == [("smoke", {}, "slack:alice")]


def test_run_rejects_unsupported_kind():
    reply = handle_slash_command("run flaky", requested_by="slack:alice")
    assert reply["response_type"] == "ephemeral"
    assert "Unknown kind" in reply["text"]


def test_run_reports_enqueue_failure(monkeypatch):
    class _RejectingService:
        def enqueue(self, kind, params, *, requested_by=""):
            raise ValueError("seat limit exceeded")

    monkeypatch.setattr(durable_jobs, "get_service", lambda: _RejectingService())

    reply = handle_slash_command("run smoke", requested_by="slack:alice")

    assert reply["response_type"] == "ephemeral"
    assert "Could not start job" in reply["text"]
    assert "seat limit exceeded" not in reply["text"]


def test_status_reports_known_job(monkeypatch):
    fake_store = _FakeStore({"id": "job-123", "kind": "smoke", "status": "running"})
    monkeypatch.setattr(persistence_store, "get_store", lambda: fake_store)

    reply = handle_slash_command("status job-123", requested_by="slack:alice")

    assert reply["response_type"] == "ephemeral"
    assert "running" in reply["text"]


def test_status_reports_unknown_job(monkeypatch):
    fake_store = _FakeStore(None)
    monkeypatch.setattr(persistence_store, "get_store", lambda: fake_store)

    reply = handle_slash_command("status missing-id", requested_by="slack:alice")

    assert "No job found" in reply["text"]


def test_blank_or_malformed_text_returns_usage():
    assert "Usage" in handle_slash_command("", requested_by="slack:alice")["text"]
    assert "Usage" in handle_slash_command("run", requested_by="slack:alice")["text"]
    assert "Usage" in handle_slash_command("frobnicate smoke", requested_by="slack:alice")["text"]
