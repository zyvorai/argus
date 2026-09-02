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

"""db_assert's sandboxed query-and-assert runner.

Deliberately NOT LLM-generated (unlike exploit_poc/host_pentest/
cloud_pentest's poc_generator.py) -- this is a single fixed script checked
into the repo. The query and assertion are declarative data, passed in via
env vars, never embedded in generated code, so there's nothing to generate
and nothing to hash-and-audit as "the code that ran" -- the code is always
this file; the auditable, per-run artifact is the query + assertion text
themselves (see orchestrator/dashboard/jobs.py::_job_db_assert's audit call).

Self-contained on purpose: this runs inside a minimal sandbox image with
only the standard library and a database driver installed (see
orchestrator/security/sandbox.py::db_image()) -- it must not import anything
else from this repo.

Reads from the environment: ZYVOR_DB_ENGINE (postgres|mysql|sqlite),
ZYVOR_DB_SECRET (the resolved connection string -- a DSN for postgres/mysql,
a filesystem path or ':memory:' for sqlite), ZYVOR_DB_QUERY,
ZYVOR_DB_QUERY_PARAMS (JSON list), ZYVOR_DB_ASSERTION (JSON object),
ZYVOR_DB_TIMEOUT_S. Prints the same 'VERIFIED: true/false - reason' line
every other sandboxed verification kind prints (parsed by
orchestrator/dashboard/jobs.py::_parse_verified_output), plus a
'ROW_COUNT: N' line.
"""

from __future__ import annotations

import json
import os
import sys


def _run_query(engine: str, secret: str, query: str, params: list, timeout_s: int):
    if engine == "postgres":
        import psycopg

        with psycopg.connect(secret, connect_timeout=timeout_s) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                columns = [d.name for d in cur.description] if cur.description else []
                rows = [tuple(row) for row in cur.fetchall()]
        return rows, columns

    if engine == "mysql":
        import pymysql
        from urllib.parse import urlsplit

        parsed = urlsplit(secret)
        conn = pymysql.connect(
            host=parsed.hostname or "localhost",
            port=parsed.port or 3306,
            user=parsed.username or "",
            password=parsed.password or "",
            database=(parsed.path or "/").lstrip("/"),
            connect_timeout=timeout_s,
        )
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                columns = [d[0] for d in cur.description] if cur.description else []
                rows = [tuple(row) for row in cur.fetchall()]
        finally:
            conn.close()
        return rows, columns

    if engine == "sqlite":
        import sqlite3

        sqlite_conn = sqlite3.connect(secret, timeout=timeout_s)
        try:
            sqlite_cur = sqlite_conn.execute(query, params)
            columns = [d[0] for d in sqlite_cur.description] if sqlite_cur.description else []
            rows = [tuple(row) for row in sqlite_cur.fetchall()]
        finally:
            sqlite_conn.close()
        return rows, columns

    raise ValueError(f"unsupported engine: {engine!r}")


def _compare(actual, op: str, expected) -> bool:
    if op == "==":
        return actual == expected
    if op == "!=":
        return actual != expected
    if op == ">":
        return actual > expected
    if op == ">=":
        return actual >= expected
    if op == "<":
        return actual < expected
    if op == "<=":
        return actual <= expected
    raise ValueError(f"unsupported comparison op: {op!r}")


def _evaluate_assertion(assertion: dict, rows: list, columns: list) -> tuple[bool, str]:
    mode = assertion.get("mode")

    if mode == "row_count":
        op = assertion.get("op", "==")
        expected = assertion.get("value")
        actual = len(rows)
        ok = _compare(actual, op, expected)
        return ok, f"row_count {actual} {'satisfies' if ok else 'does not satisfy'} {op} {expected}"

    if mode == "cell_equals":
        row_idx = assertion.get("row", 0)
        column = assertion.get("column")
        expected = assertion.get("value")
        if row_idx >= len(rows):
            return False, f"row index {row_idx} out of range ({len(rows)} row(s) returned)"
        if column not in columns:
            return False, f"column {column!r} not in result columns {columns}"
        actual = rows[row_idx][columns.index(column)]
        ok = actual == expected
        return ok, f"cell [{row_idx}][{column!r}] = {actual!r} {'==' if ok else '!='} {expected!r}"

    if mode == "column_values":
        column = assertion.get("column")
        op = assertion.get("op", "all_equal")
        expected = assertion.get("value")
        if column not in columns:
            return False, f"column {column!r} not in result columns {columns}"
        values = [row[columns.index(column)] for row in rows]
        if op == "all_equal":
            ok = all(v == expected for v in values)
            return ok, f"column {column!r} values {values} {'all equal to' if ok else 'not all equal to'} {expected!r}"
        return False, f"unsupported column_values op: {op!r}"

    return False, f"unsupported assertion mode: {mode!r}"


def main() -> int:
    engine = os.environ.get("ZYVOR_DB_ENGINE", "")
    secret = os.environ.get("ZYVOR_DB_SECRET", "")
    query = os.environ.get("ZYVOR_DB_QUERY", "")
    timeout_s = int(os.environ.get("ZYVOR_DB_TIMEOUT_S", "30"))

    try:
        query_params = json.loads(os.environ.get("ZYVOR_DB_QUERY_PARAMS", "[]"))
        assertion = json.loads(os.environ.get("ZYVOR_DB_ASSERTION", "{}"))
    except json.JSONDecodeError as exc:
        print(f"VERIFIED: false - malformed query_params/assertion JSON: {exc}")
        return 0

    try:
        rows, columns = _run_query(engine, secret, query, query_params, timeout_s)
    except Exception as exc:
        print(f"VERIFIED: false - query failed: {exc}")
        return 0

    try:
        ok, reason = _evaluate_assertion(assertion, rows, columns)
    except Exception as exc:
        print(f"VERIFIED: false - assertion evaluation failed: {exc}")
        return 0

    print(f"VERIFIED: {'true' if ok else 'false'} - {reason}")
    print(f"ROW_COUNT: {len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
