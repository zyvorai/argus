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

"""Tests for the findings store and auto-collection ('what's broken')."""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture()
def findings():
    from orchestrator.dashboard import findings as f

    importlib.reload(f)
    f.clear()
    return f


def test_add_and_listing(findings):
    findings.add("api_contract", "high", "GET /x broke", "boom", "https://x.io", "GET /x")
    L = findings.listing()
    assert L["total"] == 1
    assert L["counts"]["high"] == 1
    assert L["findings"][0]["title"] == "GET /x broke"


def test_invalid_severity_defaults_medium(findings):
    findings.add("vitals", "banana", "slow")
    assert findings.listing()["findings"][0]["severity"] == "medium"


def test_severity_filter(findings):
    findings.add("a", "high", "h")
    findings.add("b", "low", "l")
    assert findings.listing(severity="high")["total"] == 1
    assert findings.listing(severity="low")["findings"][0]["title"] == "l"


def test_clear(findings):
    findings.add("a", "high", "h")
    assert findings.clear() == 1
    assert findings.listing()["total"] == 0


def test_newest_first(findings):
    findings.add("a", "high", "first")
    findings.add("a", "high", "second")
    assert findings.listing()["findings"][0]["title"] == "second"


def test_auto_findings_api_contract(findings, monkeypatch):
    from orchestrator.dashboard import jobs

    monkeypatch.setattr(jobs, "log_progress", lambda *a, **k: None)
    jobs._auto_findings("api_contract", "https://api.x.io", {"endpoints": [
        {"method": "GET", "path": "/u", "status": 200, "ok": False, "schema_errors": ["$.email: required property missing"]},
        {"method": "GET", "path": "/ok", "status": 200, "ok": True, "schema_errors": []},
    ]})
    L = findings.listing()
    assert L["total"] == 1  # only the failing endpoint
    assert "schema violation" in L["findings"][0]["title"]


def test_auto_findings_vitals_grades(findings, monkeypatch):
    from orchestrator.dashboard import jobs

    monkeypatch.setattr(jobs, "log_progress", lambda *a, **k: None)
    jobs._auto_findings("vitals", "https://x.io", {"metrics": {
        "LCP": {"value": 5000, "grade": "poor"},
        "TTFB": {"value": 1080, "grade": "needs-improvement"},
        "CLS": {"value": 0.01, "grade": "good"},
    }})
    counts = findings.listing()["counts"]
    assert counts["high"] == 1 and counts["medium"] == 1  # poor→high, ni→medium, good→none


def test_auto_findings_auth_failures_are_high(findings, monkeypatch):
    from orchestrator.dashboard import jobs

    monkeypatch.setattr(jobs, "log_progress", lambda *a, **k: None)
    jobs._auto_findings("auth_test", "https://x.io", {"checks": [
        {"name": "unauthenticated gated", "ok": False, "detail": "reachable"},
        {"name": "api login", "ok": True, "detail": ""},
    ]})
    L = findings.listing()
    assert L["total"] == 1 and L["findings"][0]["severity"] == "high"


def test_auto_findings_misconfig_scan_compliance_signals(findings, monkeypatch):
    """The three compliance checks (security.txt, consent, PII) each raise
    at most one finding per real issue -- in particular, a not-found
    security.txt must not double-count (its own "not found" message already
    lives in `issues`, see the fix in _auto_findings)."""
    from orchestrator.dashboard import jobs

    monkeypatch.setattr(jobs, "log_progress", lambda *a, **k: None)
    jobs._auto_findings("misconfig_scan", "https://x.io", {
        "paths": {"exposed": []}, "headers": {"issues": [], "status": "ok"}, "dns": {"issues": []},
        "compliance": {
            "security_txt": {"checked": True, "found": False,
                              "issues": ["no security.txt found at /.well-known/security.txt or /security.txt"]},
            "consent": {"checked": True, "found": False, "markers": []},
            "pii": {"checked": True, "issues": ["Luhn-valid credit-card-shaped value found in response body"]},
        },
    })
    L = findings.listing()
    assert L["total"] == 3
    categories = {f["category"] for f in L["findings"]}
    assert categories == {"missing-security-txt", "no-consent-mechanism", "pii-exposure"}
    pii = next(f for f in L["findings"] if f["category"] == "pii-exposure")
    assert pii["severity"] == "high"


def test_auto_findings_misconfig_scan_security_txt_found_and_complete_raises_nothing(findings, monkeypatch):
    from orchestrator.dashboard import jobs

    monkeypatch.setattr(jobs, "log_progress", lambda *a, **k: None)
    jobs._auto_findings("misconfig_scan", "https://x.io", {
        "paths": {"exposed": []}, "headers": {"issues": [], "status": "ok"}, "dns": {"issues": []},
        "compliance": {
            "security_txt": {"checked": True, "found": True, "issues": []},
            "consent": {"checked": True, "found": True, "markers": ["onetrust"]},
            "pii": {"checked": True, "issues": []},
        },
    })
    assert findings.listing()["total"] == 0


def test_auto_findings_api_contract_diff_only_raises_breaking_changes(findings, monkeypatch):
    from orchestrator.dashboard import jobs

    monkeypatch.setattr(jobs, "log_progress", lambda *a, **k: None)
    jobs._auto_findings("api_contract_diff", "spec_a vs spec_b", {"changes": [
        {"classification": "breaking", "rule": "removed-endpoint", "where": "GET /users",
         "message": "GET /users removed"},
        {"classification": "non_breaking", "rule": "added-endpoint", "where": "GET /orders",
         "message": "GET /orders added"},
    ]})
    L = findings.listing()
    assert L["total"] == 1
    assert L["findings"][0]["category"] == "breaking-api-change"
    assert L["findings"][0]["severity"] == "high"


def test_auto_findings_contract_verify_only_raises_failed_checks(findings, monkeypatch):
    from orchestrator.dashboard import jobs

    monkeypatch.setattr(jobs, "log_progress", lambda *a, **k: None)
    jobs._auto_findings("contract_verify", "https://x.io", {"checks": [
        {"name": "GET /users/1", "ok": False, "detail": "missing required key 'email'"},
        {"name": "GET /users/2", "ok": True, "detail": ""},
    ]})
    L = findings.listing()
    assert L["total"] == 1
    assert L["findings"][0]["severity"] == "high"
    assert L["findings"][0]["category"] == "contract-violation"


def test_auto_findings_sca_scan_license_and_dependency_findings(findings, monkeypatch):
    from orchestrator.dashboard import jobs

    monkeypatch.setattr(jobs, "log_progress", lambda *a, **k: None)
    jobs._auto_findings("sca_scan", "https://x.io", {
        "blackbox": {"libraries": [
            {"product": "WordPress", "version": "6.4", "license": "GPL-2.0-or-later", "risk": "copyleft-or-restricted"},
            {"product": "jQuery", "version": "3.4.1", "license": "MIT", "risk": None},
        ]},
        "local": {"vulnerabilities": [
            {"product": "requests", "version": "2.19.1", "id": "PYSEC-2018-28", "detail": "leaks creds",
             "severity": "medium"},
        ]},
    })
    L = findings.listing()
    assert L["total"] == 2
    categories = {f["category"] for f in L["findings"]}
    assert categories == {"license-risk", "outdated-dependency"}
