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

"""SELECT-only enforcement for `db_assert` (see ROADMAP.md's "database
testing" section). Mirrors `target_policy.py`'s validate-before-execute
shape: a keyword denylist checked before persistence, not a claim of being
unbypassable. The real backstop is that the database role behind the
`db_assert` credential must itself be granted read-only access -- an IAM
control this module cannot verify, the same posture `host_pentest` takes
toward SSH account scoping.

Known, accepted gaps (documented rather than silently missed): this is a
keyword/shape check, not a real SQL parser, so an engine-specific construct
this list doesn't know about (e.g. a vendor-specific side-effecting
function call inside an otherwise-valid SELECT) could slip through. Multi-
statement batching is rejected outright rather than attempting to validate
each statement, since that's both simpler and safer.
"""

from __future__ import annotations

import re

_COMMENT_RE = re.compile(r"--[^\n]*|/\*.*?\*/", re.DOTALL)
_LEADING_CTE_RE = re.compile(r"^\s*WITH\b", re.IGNORECASE)
_LEADING_SELECT_RE = re.compile(r"^\s*SELECT\b", re.IGNORECASE)

_DENYLISTED_KEYWORDS = (
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "GRANT", "REVOKE",
    "CREATE", "EXEC", "EXECUTE", "CALL", "MERGE", "COPY", "VACUUM", "ATTACH", "PRAGMA",
    "INTO OUTFILE", "INTO DUMPFILE",
)
_DENYLISTED_KEYWORD_RE = re.compile(
    r"\b(" + "|".join(re.escape(kw) for kw in _DENYLISTED_KEYWORDS) + r")\b", re.IGNORECASE
)


class SqlGuardError(ValueError):
    pass


def validate_select_only(query: str) -> str:
    """Returns `query` unchanged if it passes; raises `SqlGuardError`
    otherwise. Callers pass the *original* query through to execution --
    this only validates, it doesn't rewrite."""
    if not query or not query.strip():
        raise SqlGuardError("query must not be empty")

    normalized = _COMMENT_RE.sub(" ", query).strip()
    if not normalized:
        raise SqlGuardError("query contains no statement outside of comments")

    # Reject multi-statement input -- one optional trailing semicolon is
    # tolerated, anything else (a second statement) is not.
    body = normalized[:-1] if normalized.endswith(";") else normalized
    if ";" in body:
        raise SqlGuardError("multi-statement queries are not allowed -- one SELECT only")

    if not (_LEADING_SELECT_RE.match(body) or _LEADING_CTE_RE.match(body)):
        raise SqlGuardError("query must start with SELECT (or WITH ... SELECT)")

    match = _DENYLISTED_KEYWORD_RE.search(body)
    if match:
        raise SqlGuardError(f"query contains a disallowed keyword: {match.group(1).upper()}")

    return query
