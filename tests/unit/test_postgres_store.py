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

"""Integration tests for PostgresStore against a real Postgres instance.

Requires TEST_POSTGRES_DSN (a real postgresql:// URL) and the `postgres`
extra installed — skipped entirely otherwise, so `pytest` still runs clean
for anyone without a local Postgres (the CI `postgres-quality` job in
.github/workflows/security.yml sets TEST_POSTGRES_DSN against a real
`postgres:` service container, so this isn't just locally-verified-once).

Each test gets its own schema (CREATE SCHEMA ... search_path), not a shared
database, so tests can run in any order without clobbering each other's rows.
"""

from __future__ import annotations

import os
import threading
import uuid

import pytest

psycopg = pytest.importorskip("psycopg")

TEST_DSN = os.environ.get("TEST_POSTGRES_DSN", "")
pytestmark = pytest.mark.skipif(not TEST_DSN, reason="TEST_POSTGRES_DSN not set")


@pytest.fixture
def store():
    from orchestrator.persistence.postgres_store import PostgresStore

    schema = f"test_{uuid.uuid4().hex[:16]}"
    with psycopg.connect(TEST_DSN, autocommit=True) as conn:
        conn.execute(f'CREATE SCHEMA "{schema}"')
    dsn = f"{TEST_DSN}{'&' if '?' in TEST_DSN else '?'}options=-csearch_path%3D{schema}"
    instance = PostgresStore(dsn)
    yield instance
    with psycopg.connect(TEST_DSN, autocommit=True) as conn:
        conn.execute(f'DROP SCHEMA "{schema}" CASCADE')


def test_migrate_is_idempotent(store):
    store.migrate()  # a second pass must not error


def test_job_lifecycle(store):
    job = store.enqueue_job("smoke", {"url": "https://example.com"}, requested_by="tester")
    assert job["status"] == "queued"

    claimed = store.claim_job()
    assert claimed["id"] == job["id"]
    assert claimed["status"] == "running"
    assert store.claim_job() is None  # nothing else queued

    store.heartbeat(claimed["id"])
    store.finish_job(claimed["id"], result={"passed": 1})
    finished = store.get_job(claimed["id"])
    assert finished["status"] == "succeeded"
    assert finished["result"] == {"passed": 1}


def test_trace_context_round_trips_through_enqueue_and_claim(store):
    """Same cross-replica trace propagation contract as MissionControlStore
    (tests/unit/test_persistence_store.py) -- PostgresStore is a drop-in, so
    a traceparent persisted at enqueue time must survive a claim exactly the
    same way."""
    traceparent = "00-30957595af83ba0d07f0a11ce2733726-097cdd883f795456-01"
    job = store.enqueue_job("smoke", {}, trace_context=traceparent)
    assert job["trace_context"] == traceparent

    claimed = store.claim_job()
    assert claimed["trace_context"] == traceparent


def test_enqueue_job_idempotency_key_returns_existing_row(store):
    first = store.enqueue_job("smoke", {"url": "https://x.com"}, idempotency_key="k1")
    second = store.enqueue_job("smoke", {"url": "https://x.com"}, idempotency_key="k1")
    assert first["id"] == second["id"]


def test_claim_job_never_double_claims_under_concurrency(store):
    job_ids = [store.enqueue_job("smoke", {"i": i})["id"] for i in range(10)]
    claimed: list[str] = []
    lock = threading.Lock()

    def worker():
        job = store.claim_job()
        if job:
            with lock:
                claimed.append(job["id"])

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(claimed) == sorted(job_ids)
    assert len(set(claimed)) == 10


def test_schedule_lifecycle(store):
    sched = store.add_schedule("smoke", {"url": "https://x.com"}, 60, requested_by="tester")
    assert sched["interval_s"] == 60
    store.advance_schedule(sched["id"], ran=True)
    updated = store.get_schedule(sched["id"])
    assert updated["runs"] == 1
    assert store.remove_schedule(sched["id"]) is True
    assert store.get_schedule(sched["id"]) is None


def test_finding_fingerprint_dedup(store):
    first_id = store.add_finding("scan", "high", "exposed .env", fingerprint="fp-1")
    second_id = store.add_finding("scan", "high", "exposed .env (again)", fingerprint="fp-1")
    assert first_id == second_id
    result = store.list_findings()
    assert result["total"] == 1
    assert result["findings"][0]["occurrences"] == 2
    assert store.clear_findings() == 1


def test_engagement_lifecycle(store):
    eng = store.create_engagement(
        "example.com", "authorized test", "active_recon", authorized_by="admin"
    )
    assert store.get_engagement(eng["id"])["target_pattern"] == "example.com"
    assert store.revoke_engagement(eng["id"], revoked_by="admin") is True
    assert store.revoke_engagement(eng["id"], revoked_by="admin") is False  # already revoked


def test_audit_and_webhook_replay(store):
    store.audit("job.enqueue", actor="tester", detail={"k": "v"})
    events = store.list_audit()
    assert events[0]["action"] == "job.enqueue"
    assert events[0]["detail"] == {"k": "v"}

    assert store.record_webhook_delivery("d1", "push", "sha") is True
    assert store.record_webhook_delivery("d1", "push", "sha") is False


def test_requirement_versioning_and_traceability(store):
    v1 = store.upsert_requirement(
        "req-pg", source_type="document", origin_id="spec.md",
        title="PG test", content={"d": "v1"}, quality_score=90.0,
    )
    assert v1["is_new_version"] is True
    assert v1["latest_version"] == 1

    unchanged = store.upsert_requirement(
        "req-pg", source_type="document", origin_id="spec.md",
        title="PG test", content={"d": "v1"}, quality_score=90.0,
    )
    assert unchanged["is_new_version"] is False

    store.link_requirement_test("req-pg", "tests/generated/pg.spec.ts")

    v2 = store.upsert_requirement(
        "req-pg", source_type="document", origin_id="spec.md",
        title="PG test", content={"d": "v2"}, quality_score=95.0,
    )
    assert v2["is_new_version"] is True
    assert v2["latest_version"] == 2
    assert v2["previous_version"] == 1

    assert store.linked_tests("req-pg", 1) == ["tests/generated/pg.spec.ts"]
    assert store.linked_tests("req-pg", 2) == []
    assert [h["version"] for h in store.requirement_history("req-pg")] == [1, 2]

    fetched = store.get_requirement("req-pg")
    assert fetched["content"] == {"d": "v2"}
    assert fetched["quality_score"] == 95.0


def test_upsert_requirement_concurrent_first_insert_is_race_free(store):
    errors: list[Exception] = []

    def worker():
        try:
            store.upsert_requirement(
                "req-race", source_type="github", origin_id="issue-1.md",
                title="Race", content={"d": "same"},
            )
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    assert len(store.requirement_history("req-race")) == 1


def test_get_store_dispatches_to_postgres(monkeypatch):
    monkeypatch.setenv("ZYVOR_STATE_DB", TEST_DSN)
    import orchestrator.persistence.store as store_module

    monkeypatch.setattr(store_module, "_default_store", None)
    instance = store_module.get_store()
    try:
        assert type(instance).__name__ == "PostgresStore"
    finally:
        monkeypatch.setattr(store_module, "_default_store", None)
