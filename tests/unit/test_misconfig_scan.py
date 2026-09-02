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

"""Unit tests for the compliance-signal checks added to
agents/probes/misconfig_scan.py (security.txt, consent-mechanism heuristic,
PII-pattern scan)."""

from __future__ import annotations

import httpx

import agents.probes.misconfig_scan as misconfig_scan
from agents.probes.misconfig_scan import (
    check_consent_signals,
    check_security_txt,
    scan_pii_patterns,
)


def _client_for(handler):
    def _client(insecure: bool = False):
        return httpx.Client(transport=httpx.MockTransport(handler))

    return _client


def test_check_consent_signals_finds_a_known_cmp_marker():
    body = '<html><head><script src="https://cdn.cookielaw.org/onetrust.js"></script></head></html>'
    result = check_consent_signals(body)
    assert result["checked"] is True
    assert result["found"] is True
    assert "onetrust" in result["markers"]


def test_check_consent_signals_no_marker_found():
    body = "<html><body><h1>Welcome</h1></body></html>"
    result = check_consent_signals(body)
    assert result["found"] is False
    assert result["markers"] == []


def test_scan_pii_patterns_flags_ssn_shaped_value():
    result = scan_pii_patterns("customer ssn on file: 123-45-6789")
    assert any("SSN" in issue for issue in result["issues"])


def test_scan_pii_patterns_flags_luhn_valid_card_number():
    # 4111111111111111 is the standard Luhn-valid Visa test number.
    result = scan_pii_patterns('{"card": "4111111111111111"}')
    assert any("credit-card" in issue for issue in result["issues"])


def test_scan_pii_patterns_ignores_luhn_invalid_digit_sequences():
    # A 16-digit sequence that is NOT Luhn-valid (e.g. a random order/tracking ID).
    result = scan_pii_patterns('{"order_id": "1234567890123456"}')
    assert result["issues"] == []


def test_scan_pii_patterns_clean_body_has_no_issues():
    result = scan_pii_patterns("<html><body>Welcome to our site</body></html>")
    assert result == {"checked": True, "issues": []}


def test_check_security_txt_found_with_required_fields(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/.well-known/security.txt":
            return httpx.Response(200, text="Contact: mailto:security@example.com\nExpires: 2030-01-01T00:00:00Z\n")
        return httpx.Response(404)

    monkeypatch.setattr(misconfig_scan, "_client", _client_for(handler))
    result = check_security_txt("https://example.com/")
    assert result["checked"] is True
    assert result["found"] is True
    assert result["issues"] == []


def test_check_security_txt_found_but_missing_required_field(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/.well-known/security.txt":
            return httpx.Response(200, text="Contact: mailto:security@example.com\n")
        return httpx.Response(404)

    monkeypatch.setattr(misconfig_scan, "_client", _client_for(handler))
    result = check_security_txt("https://example.com/")
    assert result["found"] is True
    assert "security.txt missing required Expires field" in result["issues"]


def test_check_security_txt_falls_back_to_legacy_path(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/security.txt":
            return httpx.Response(200, text="Contact: mailto:security@example.com\nExpires: 2030-01-01T00:00:00Z\n")
        return httpx.Response(404)

    monkeypatch.setattr(misconfig_scan, "_client", _client_for(handler))
    result = check_security_txt("https://example.com/")
    assert result["found"] is True


def test_check_security_txt_not_found_anywhere(monkeypatch):
    monkeypatch.setattr(misconfig_scan, "_client", _client_for(lambda request: httpx.Response(404)))
    result = check_security_txt("https://example.com/")
    assert result["checked"] is True
    assert result["found"] is False
    assert result["issues"]


def test_check_security_txt_degrades_gracefully_when_unreachable(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    monkeypatch.setattr(misconfig_scan, "_client", _client_for(handler))
    result = check_security_txt("https://example.com/")
    assert result == {"checked": False, "found": False, "issues": []}
