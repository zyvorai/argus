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

"""Unit tests for orchestrator/security/sql_guard.py -- db_assert's
SELECT-only enforcement."""

from __future__ import annotations

import pytest

from orchestrator.security.sql_guard import SqlGuardError, validate_select_only


@pytest.mark.parametrize("query", [
    "SELECT * FROM orders",
    "  select id from users  ",
    "SELECT * FROM orders;",
    "WITH recent AS (SELECT * FROM orders) SELECT * FROM recent",
    "select * from orders -- trailing comment",
    "SELECT * FROM orders WHERE id = %s",
])
def test_accepts_valid_select_only_queries(query):
    assert validate_select_only(query) == query


def test_empty_query_rejected():
    with pytest.raises(SqlGuardError, match="empty"):
        validate_select_only("")


def test_whitespace_only_query_rejected():
    with pytest.raises(SqlGuardError, match="empty"):
        validate_select_only("   ")


def test_comment_only_query_rejected():
    with pytest.raises(SqlGuardError, match="no statement"):
        validate_select_only("-- just a comment")


@pytest.mark.parametrize("query", [
    "DROP TABLE orders",
    "INSERT INTO orders VALUES (1)",
    "UPDATE orders SET status = 'x'",
    "DELETE FROM orders",
    "CREATE TABLE x (id INT)",
])
def test_rejects_non_select_statements(query):
    with pytest.raises(SqlGuardError, match="must start with SELECT"):
        validate_select_only(query)


@pytest.mark.parametrize("query", [
    "SELECT * FROM orders; DROP TABLE orders",
    "SELECT 1; SELECT 2",
])
def test_rejects_multi_statement_queries(query):
    with pytest.raises(SqlGuardError, match="multi-statement"):
        validate_select_only(query)


def test_denylisted_keyword_after_a_select_prefix_still_rejected():
    query = "SELECT * FROM orders WHERE 1=1; DROP TABLE x --"
    # A crafted query that starts with SELECT but smuggles a mutating
    # statement after a semicolon is still caught by the multi-statement
    # check first -- confirms defense-in-depth, not just the keyword scan.
    with pytest.raises(SqlGuardError):
        validate_select_only(query)


def test_rejects_pragma_for_sqlite_mutation_risk():
    with pytest.raises(SqlGuardError, match="PRAGMA"):
        validate_select_only("SELECT * FROM (PRAGMA table_info(orders))")


def test_case_insensitive_keyword_matching():
    with pytest.raises(SqlGuardError, match="must start with SELECT"):
        validate_select_only("delete from orders")


def test_returns_original_query_unchanged_not_a_rewrite():
    query = "SELECT   *   FROM orders"  # unusual spacing, deliberately not normalized in the return value
    assert validate_select_only(query) == query
