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

"""End-to-end CSRF check through the real FastAPI app: log in (which issues
both the session and CSRF cookies), then confirm a mutating dashboard
request is rejected without X-CSRF-Token and accepted with it. Uses
DELETE /api/dashboard/pods/{name} as the mutating target purely because it
degrades gracefully with no cluster (`{"ok": False, "error": "cluster
unavailable"}`) — this test is about the CSRF gate in front of the handler,
not the handler's own behavior."""

from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient

from orchestrator.security import rate_limit


@pytest.fixture(autouse=True)
def _dashboard_password(monkeypatch):
    monkeypatch.setenv("DASHBOARD_PASSWORD", "Admin@321")
    monkeypatch.setenv("DASHBOARD_USER", "admin")
    from orchestrator.dashboard import auth as auth_mod

    importlib.reload(auth_mod)  # fresh login-lockout state per test, matches test_auth.py
    rate_limit.reset()


def _logged_in_client():
    from orchestrator.webhook import create_app

    client = TestClient(create_app())
    response = client.post("/api/login", json={"username": "admin", "password": "Admin@321"})
    assert response.status_code == 200
    return client


def test_mutating_request_without_csrf_header_is_rejected():
    client = _logged_in_client()

    response = client.delete("/api/dashboard/pods/some-pod")

    assert response.status_code == 403
    assert "CSRF" in response.json()["detail"]


def test_mutating_request_with_correct_csrf_header_is_accepted():
    client = _logged_in_client()
    csrf_cookie = client.cookies.get("zyvor_qa_csrf")
    assert csrf_cookie

    response = client.delete(
        "/api/dashboard/pods/some-pod", headers={"X-CSRF-Token": csrf_cookie}
    )

    assert response.status_code != 403


def test_mutating_request_with_wrong_csrf_header_is_rejected():
    client = _logged_in_client()

    response = client.delete(
        "/api/dashboard/pods/some-pod", headers={"X-CSRF-Token": "not-the-right-value"}
    )

    assert response.status_code == 403


def test_get_requests_are_not_csrf_checked():
    client = _logged_in_client()

    response = client.get("/api/dashboard/overview")

    assert response.status_code != 403


def test_relogin_while_authenticated_does_not_require_csrf():
    """Visiting /login with a live session and signing in again must work
    without X-CSRF-Token — the login form is an open credential gate."""
    client = _logged_in_client()

    response = client.post(
        "/api/login", json={"username": "admin", "password": "Admin@321"}
    )

    assert response.status_code == 200
    assert response.json().get("ok") is True
