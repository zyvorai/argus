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

"""Unit tests for agents/db_assert/runner_script.py -- the deterministic
(not LLM-generated) query-and-assert script that runs inside the db_assert
sandbox. Pure-function tests import it directly; the end-to-end test
actually spawns it as a subprocess (exactly `python3 <file>`, the same
invocation the sandbox uses) against a real SQLite database, since SQLite
needs no server and is fully live-testable in this environment (unlike
Postgres/MySQL, which were live-verified manually against real instances
during development but aren't spun up in CI)."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from agents.db_assert.engine import load_runner_script
from agents.db_assert.runner_script import _compare, _evaluate_assertion, _run_query

RUNNER_PATH = Path(__file__).resolve().parents[2] / "agents" / "db_assert" / "runner_script.py"


# -- pure functions ---------------------------------------------------------

def test_compare_operators():
    assert _compare(5, "==", 5) is True
    assert _compare(5, "!=", 6) is True
    assert _compare(5, ">", 4) is True
    assert _compare(5, ">=", 5) is True
    assert _compare(4, "<", 5) is True
    assert _compare(5, "<=", 5) is True
    assert _compare(5, "==", 6) is False


def test_evaluate_row_count():
    ok, _ = _evaluate_assertion({"mode": "row_count", "op": "==", "value": 2}, [(1,), (2,)], ["id"])
    assert ok is True
    ok, _ = _evaluate_assertion({"mode": "row_count", "op": "==", "value": 3}, [(1,), (2,)], ["id"])
    assert ok is False


def test_evaluate_cell_equals():
    rows = [(1, "completed")]
    columns = ["id", "status"]
    ok, _ = _evaluate_assertion({"mode": "cell_equals", "row": 0, "column": "status", "value": "completed"}, rows, columns)
    assert ok is True
    ok, _ = _evaluate_assertion({"mode": "cell_equals", "row": 0, "column": "status", "value": "pending"}, rows, columns)
    assert ok is False


def test_evaluate_cell_equals_row_out_of_range():
    ok, reason = _evaluate_assertion({"mode": "cell_equals", "row": 5, "column": "status", "value": "x"}, [], ["status"])
    assert ok is False
    assert "out of range" in reason


def test_evaluate_cell_equals_unknown_column():
    ok, reason = _evaluate_assertion({"mode": "cell_equals", "row": 0, "column": "nope", "value": "x"}, [(1,)], ["id"])
    assert ok is False
    assert "not in result columns" in reason


def test_evaluate_column_values_all_equal():
    rows = [("pending",), ("pending",)]
    ok, _ = _evaluate_assertion({"mode": "column_values", "column": "status", "op": "all_equal", "value": "pending"}, rows, ["status"])
    assert ok is True
    rows = [("pending",), ("shipped",)]
    ok, _ = _evaluate_assertion({"mode": "column_values", "column": "status", "op": "all_equal", "value": "pending"}, rows, ["status"])
    assert ok is False


def test_evaluate_unsupported_mode():
    ok, reason = _evaluate_assertion({"mode": "bogus"}, [], [])
    assert ok is False
    assert "unsupported assertion mode" in reason


def test_run_query_sqlite(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE orders (id INTEGER, status TEXT)")
    conn.execute("INSERT INTO orders VALUES (1, 'completed')")
    conn.commit()
    conn.close()

    rows, columns = _run_query("sqlite", db_path, "SELECT id, status FROM orders WHERE id = ?", [1], 10)
    assert rows == [(1, "completed")]
    assert columns == ["id", "status"]


def test_run_query_unsupported_engine():
    import pytest

    with pytest.raises(ValueError, match="unsupported engine"):
        _run_query("mssql", "whatever", "SELECT 1", [], 10)


def test_load_runner_script_returns_real_file_contents():
    script = load_runner_script()
    assert "def main()" in script
    assert script == RUNNER_PATH.read_text(encoding="utf-8")


# -- real subprocess, exactly the sandbox invocation, against real SQLite --

def _run_script(env_overrides: dict) -> subprocess.CompletedProcess:
    env = {**os.environ, **env_overrides}
    return subprocess.run([sys.executable, str(RUNNER_PATH)], env=env, capture_output=True, text=True, timeout=15)


def test_end_to_end_subprocess_pass(tmp_path):
    db_path = str(tmp_path / "orders.db")
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE orders (id INTEGER, status TEXT)")
    conn.execute("INSERT INTO orders VALUES (1, 'completed')")
    conn.commit()
    conn.close()

    proc = _run_script({
        "ZYVOR_DB_ENGINE": "sqlite", "ZYVOR_DB_SECRET": db_path,
        "ZYVOR_DB_QUERY": "SELECT * FROM orders WHERE status = ?",
        "ZYVOR_DB_QUERY_PARAMS": json.dumps(["completed"]),
        "ZYVOR_DB_ASSERTION": json.dumps({"mode": "row_count", "op": "==", "value": 1}),
        "ZYVOR_DB_TIMEOUT_S": "10",
    })
    assert proc.returncode == 0
    assert "VERIFIED: true" in proc.stdout
    assert "ROW_COUNT: 1" in proc.stdout


def test_end_to_end_subprocess_fail(tmp_path):
    db_path = str(tmp_path / "orders.db")
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE orders (id INTEGER, status TEXT)")
    conn.execute("INSERT INTO orders VALUES (1, 'pending')")
    conn.commit()
    conn.close()

    proc = _run_script({
        "ZYVOR_DB_ENGINE": "sqlite", "ZYVOR_DB_SECRET": db_path,
        "ZYVOR_DB_QUERY": "SELECT * FROM orders WHERE status = ?",
        "ZYVOR_DB_QUERY_PARAMS": json.dumps(["completed"]),
        "ZYVOR_DB_ASSERTION": json.dumps({"mode": "row_count", "op": "==", "value": 1}),
        "ZYVOR_DB_TIMEOUT_S": "10",
    })
    assert proc.returncode == 0  # a failed assertion is still a clean run, not a crash
    assert "VERIFIED: false" in proc.stdout


def test_end_to_end_subprocess_bad_query_degrades_to_verified_false(tmp_path):
    db_path = str(tmp_path / "orders.db")
    sqlite3.connect(db_path).close()

    proc = _run_script({
        "ZYVOR_DB_ENGINE": "sqlite", "ZYVOR_DB_SECRET": db_path,
        "ZYVOR_DB_QUERY": "SELECT * FROM does_not_exist",
        "ZYVOR_DB_QUERY_PARAMS": "[]",
        "ZYVOR_DB_ASSERTION": json.dumps({"mode": "row_count", "op": "==", "value": 0}),
        "ZYVOR_DB_TIMEOUT_S": "10",
    })
    assert proc.returncode == 0
    assert "VERIFIED: false - query failed" in proc.stdout
