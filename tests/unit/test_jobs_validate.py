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

"""Unit tests for dashboard job parameter validation (orchestrator/dashboard/jobs.py)."""

from __future__ import annotations

import pytest

from orchestrator.dashboard.jobs import VALID_KINDS, _redact_params, _safe_local_spec, _validate


def test_password_redacted_but_url_kept():
    red = _redact_params({"url": "https://x.io", "username": "admin", "password": "s3cret"})
    assert red["password"] == "***"
    assert red["username"] == "admin"
    assert red["url"] == "https://x.io"


def test_redact_leaves_empty_password_untouched():
    red = _redact_params({"password": ""})
    assert red["password"] == ""  # nothing to hide


def test_redact_does_not_mutate_original():
    orig = {"password": "s3cret"}
    _redact_params(orig)
    assert orig["password"] == "s3cret"


def test_redact_bearer_token_and_api_key():
    red = _redact_params({"url": "https://x.io", "token": "eyJhbGci...", "apiKey": "sk-123"})
    assert red["token"] == "***" and red["apiKey"] == "***"
    assert red["url"] == "https://x.io"


def test_redact_nested_auth_secrets():
    red = _redact_params({"url": "https://x.io", "auth": {"token": "eyJ...", "header": "x-api-key", "apiKey": "k"}})
    assert red["auth"]["token"] == "***"
    assert red["auth"]["apiKey"] == "***"
    assert red["auth"]["header"] == "x-api-key"  # non-secret preserved


def test_flow_and_route_sweep_registered():
    assert "flow" in VALID_KINDS
    assert "route_sweep" in VALID_KINDS


def test_flow_requires_url_scheme():
    with pytest.raises(ValueError):
        _validate("flow", {"url": "zyvor.dev", "description": "go to /"})


def test_flow_requires_description():
    with pytest.raises(ValueError):
        _validate("flow", {"url": "https://zyvor.dev", "description": "  "})


def test_flow_clean_defaults():
    clean = _validate("flow", {"url": "https://zyvor.dev", "description": "go to /"})
    # TargetPolicy normalizes empty path to "/"
    assert clean["url"] in {"https://zyvor.dev", "https://zyvor.dev/"}
    assert clean["record"] is True  # default on
    assert clean["steps_mode"] is False
    assert clean["insecure"] is False


def test_flow_record_toggle_off():
    clean = _validate("flow", {"url": "https://x.io", "description": "go to /", "record": False})
    assert clean["record"] is False


def test_route_sweep_routes_filtered_and_defaulted():
    clean = _validate("route_sweep", {"url": "https://x.io", "routes": "/, /a, bad, /b"})
    assert clean["routes"] == ["/", "/a", "/b"]
    # empty → defaults to root
    clean2 = _validate("route_sweep", {"url": "https://x.io", "routes": "nothing-valid"})
    assert clean2["routes"] == ["/"]


def test_route_sweep_viewports_whitelist():
    clean = _validate("route_sweep", {"url": "https://x.io", "viewports": ["desktop", "mobile", "watch"]})
    assert clean["viewports"] == ["desktop", "mobile"]


def test_route_sweep_auto_and_max_pages():
    clean = _validate("route_sweep", {"url": "https://x.io", "auto": True, "max_pages": 999})
    assert clean["auto"] is True
    assert clean["max_pages"] == 40  # clamped


def test_unknown_kind_rejected():
    with pytest.raises(ValueError):
        _validate("not_a_real_kind", {})


def test_new_kinds_registered():
    for k in ("api_contract", "auth_test", "realtime", "vitals", "har_replay", "import_codegen"):
        assert k in VALID_KINDS


def test_har_replay_requires_url_and_mode():
    with pytest.raises(ValueError):
        _validate("har_replay", {"url": "not-a-url", "mode": "record"})
    with pytest.raises(ValueError):
        _validate("har_replay", {"url": "https://x.io", "mode": "replay"})  # no har
    clean = _validate("har_replay", {"url": "https://x.io", "mode": "record", "routes": "/,/a"})
    assert clean["mode"] == "record"
    assert clean["routes"] == ["/", "/a"]


def test_import_codegen_requires_script():
    with pytest.raises(ValueError):
        _validate("import_codegen", {"script": "  "})
    clean = _validate("import_codegen", {"script": "await page.goto('/');"})
    assert clean["run"] is False
    with pytest.raises(ValueError):
        _validate("import_codegen", {"script": "await page.goto('/');", "run": True})


def test_smoke_shard_and_grep():
    clean = _validate("smoke", {"grep": "@smoke", "shard": "1/2"})
    assert clean["grep"] == "@smoke"
    assert clean["shard"] == "1/2"
    with pytest.raises(ValueError):
        _validate("smoke", {"shard": "bad"})


def test_api_contract_requires_spec_in_spec_mode():
    with pytest.raises(ValueError):
        _validate("api_contract", {"url": "https://api.x.io", "mode": "spec"})


def test_api_contract_requires_workflow_in_workflow_mode():
    with pytest.raises(ValueError):
        _validate("api_contract", {"url": "https://api.x.io", "mode": "workflow"})


def test_api_contract_clean_spec():
    clean = _validate("api_contract", {"url": "https://api.x.io", "mode": "spec", "spec": "https://api.x.io/openapi.json"})
    assert clean["mode"] == "spec"
    assert clean["spec"] == "https://api.x.io/openapi.json"
    assert clean["max_endpoints"] == 60


def test_api_contract_max_endpoints_clamped():
    clean = _validate("api_contract", {"url": "https://api.x.io", "mode": "spec",
                                        "spec": {"paths": {}}, "max_endpoints": 9999})
    assert clean["max_endpoints"] == 200


def test_api_contract_diff_accepts_inline_specs():
    clean = _validate("api_contract_diff", {"spec_a": {"paths": {}}, "spec_b": {"paths": {}}})
    assert clean["spec_a"] == {"paths": {}}
    assert clean["fail_on"] == "breaking"


def test_api_contract_diff_validates_and_ssrf_checks_url_refs():
    clean = _validate("api_contract_diff", {
        "spec_a": "https://api.x.io/openapi.json", "spec_b": {"paths": {}},
    })
    assert clean["spec_a"] == "https://api.x.io/openapi.json"


def test_api_contract_diff_rejects_ssrf_target_for_url_ref():
    with pytest.raises(ValueError):
        _validate("api_contract_diff", {"spec_a": "http://169.254.169.254/openapi.json", "spec_b": {"paths": {}}})


def test_api_contract_diff_accepts_git_ref():
    clean = _validate("api_contract_diff", {"spec_a": "git:main:openapi.json", "spec_b": {"paths": {}}})
    assert clean["spec_a"] == "git:main:openapi.json"


def test_api_contract_diff_rejects_missing_spec():
    with pytest.raises(ValueError):
        _validate("api_contract_diff", {"spec_a": {"paths": {}}})


def test_api_contract_diff_rejects_unsupported_spec_shape():
    with pytest.raises(ValueError):
        _validate("api_contract_diff", {"spec_a": 12345, "spec_b": {"paths": {}}})


def test_api_contract_diff_fail_on_any():
    clean = _validate("api_contract_diff", {
        "spec_a": {"paths": {}}, "spec_b": {"paths": {}}, "fail_on": "any",
    })
    assert clean["fail_on"] == "any"


def test_api_contract_diff_is_not_elevated_risk():
    """Pure static diff, no live target interaction -- unlike misconfig_scan/
    cve_lookup, this kind must not require an engagement."""
    from orchestrator.dashboard.jobs import ELEVATED_RISK_KINDS

    assert "api_contract_diff" not in ELEVATED_RISK_KINDS
    # and _validate() must succeed with no engagement_id at all
    _validate("api_contract_diff", {"spec_a": {"paths": {}}, "spec_b": {"paths": {}}})


def test_vitals_requires_url_scheme():
    with pytest.raises(ValueError):
        _validate("vitals", {"url": "x.io"})


def test_vitals_throttle_whitelist():
    assert _validate("vitals", {"url": "https://x.io", "throttle": "3g"})["throttle"] == "3g"
    assert _validate("vitals", {"url": "https://x.io", "throttle": "bogus"})["throttle"] == ""


def test_auth_test_requires_a_login_method():
    with pytest.raises(ValueError):
        _validate("auth_test", {"url": "https://x.io"})
    ok = _validate("auth_test", {"url": "https://x.io", "api_login": "https://x.io/api/login"})
    assert ok["api_login"].endswith("/login")


def test_realtime_requires_a_target():
    with pytest.raises(ValueError):
        _validate("realtime", {"url": "https://x.io"})
    ok = _validate("realtime", {"url": "https://x.io", "ws": "/ws/flows", "expect_messages": 3})
    assert ok["ws"] == "/ws/flows" and ok["expect_messages"] == 3


# ── _safe_local_spec: path-traversal safety ─────────────────────────────


def test_safe_local_spec_accepts_a_real_file_inside_the_repo():
    resolved = _safe_local_spec("prompts/examples/vm-create.md")
    assert resolved.endswith("vm-create.md")
    assert "prompts" in resolved


def test_safe_local_spec_rejects_path_traversal():
    with pytest.raises(ValueError, match="inside the repository"):
        _safe_local_spec("../../../../etc/passwd")


def test_safe_local_spec_rejects_absolute_path_outside_repo():
    with pytest.raises(ValueError, match="inside the repository"):
        _safe_local_spec("/etc/passwd")


def test_safe_local_spec_rejects_missing_file():
    with pytest.raises(ValueError, match="spec not found"):
        _safe_local_spec("prompts/examples/does-not-exist.md")


def test_flaky_target_is_path_checked_unless_manual():
    clean = _validate("flaky", {"target": "manual", "runs": 5})
    assert clean["target"] == "manual"
    assert clean["runs"] == 5  # within [2, 10]
    with pytest.raises(ValueError, match="inside the repository"):
        _validate("flaky", {"target": "../../../../etc/passwd"})


def test_flaky_runs_clamped():
    assert _validate("flaky", {"runs": 1})["runs"] == 2
    assert _validate("flaky", {"runs": 999})["runs"] == 10


# ── full / generate / discover: source + spec + pr_number ───────────────


@pytest.mark.parametrize("kind", ["full", "generate"])
def test_source_defaults_to_local(kind):
    assert _validate(kind, {})["source"] == "local"


def test_discover_source_defaults_to_github():
    assert _validate("discover", {})["source"] == "github"


def test_invalid_source_rejected():
    with pytest.raises(ValueError, match="source must be"):
        _validate("full", {"source": "ftp"})


def test_full_pr_number_coerced_to_int_or_none():
    assert _validate("full", {"pr_number": "42"})["pr_number"] == 42
    assert _validate("full", {"pr_number": ""})["pr_number"] is None
    assert _validate("full", {})["pr_number"] is None


def test_full_local_spec_goes_through_safe_local_spec():
    with pytest.raises(ValueError, match="inside the repository"):
        _validate("full", {"source": "local", "spec": "../../../../etc/passwd"})


# ── create ────────────────────────────────────────────────────────────


def test_create_requires_description():
    with pytest.raises(ValueError, match="description is required"):
        _validate("create", {"description": "   "})


def test_create_description_truncated_and_execute_flag():
    clean = _validate("create", {"description": "x" * 600, "execute": True})
    assert len(clean["description"]) == 500
    assert clean["execute"] is True


# ── regression ────────────────────────────────────────────────────────


def test_regression_update_baselines_flag():
    assert _validate("regression", {})["update_baselines"] is False
    assert _validate("regression", {"update_baselines": True})["update_baselines"] is True


# ── crawl_test ────────────────────────────────────────────────────────


def test_crawl_test_requires_url_scheme():
    with pytest.raises(ValueError, match="http"):
        _validate("crawl_test", {"url": "not-a-url"})


def test_crawl_test_clamps_max_pages_and_truncates_credentials():
    clean = _validate(
        "crawl_test",
        {"url": "https://x.io", "max_pages": 9999, "username": "u" * 300, "password": "p" * 300},
    )
    assert clean["max_pages"] == 200
    assert len(clean["username"]) == 200
    assert len(clean["password"]) == 200


# ── audit ─────────────────────────────────────────────────────────────


def test_audit_requires_url_scheme():
    with pytest.raises(ValueError, match="http"):
        _validate("audit", {"url": "not-a-url"})


def test_audit_checks_filtered_to_valid_and_max_pages_clamped():
    clean = _validate("audit", {"url": "https://x.io", "checks": ["a11y", "bogus"], "max_pages": 500})
    assert clean["checks"] == ["a11y"]
    assert clean["max_pages"] == 100


def test_audit_invalid_checks_fall_back_to_default():
    clean = _validate("audit", {"url": "https://x.io", "checks": ["bogus"]})
    assert clean["checks"] == ["a11y", "seo", "console"]


# ── screenshot ────────────────────────────────────────────────────────


def test_screenshot_requires_url_scheme():
    with pytest.raises(ValueError, match="http"):
        _validate("screenshot", {"url": "not-a-url"})


def test_screenshot_viewports_filtered_and_defaulted():
    clean = _validate("screenshot", {"url": "https://x.io", "viewports": ["desktop", "watch"]})
    assert clean["viewports"] == ["desktop"]
    clean2 = _validate("screenshot", {"url": "https://x.io", "viewports": ["watch"]})
    assert clean2["viewports"] == ["desktop"]


# ── compare ───────────────────────────────────────────────────────────


def test_compare_requires_both_urls():
    with pytest.raises(ValueError, match="url_a"):
        _validate("compare", {"url_b": "https://x.io"})
    with pytest.raises(ValueError, match="url_b"):
        _validate("compare", {"url_a": "https://x.io"})
    clean = _validate("compare", {"url_a": "https://a.io", "url_b": "https://b.io"})
    assert clean["url_a"] in {"https://a.io", "https://a.io/"}
    assert clean["url_b"] in {"https://b.io", "https://b.io/"}


# ── ping ──────────────────────────────────────────────────────────────


def test_ping_requires_at_least_one_url():
    with pytest.raises(ValueError, match="at least one"):
        _validate("ping", {"urls": "not-a-url, also-bad"})


def test_ping_parses_comma_and_newline_separated_urls():
    clean = _validate("ping", {"urls": "https://a.io,https://b.io\nhttps://c.io"})
    hosts = [u.split("//", 1)[1].rstrip("/") for u in clean["urls"]]
    assert hosts == ["a.io", "b.io", "c.io"]


def test_ping_caps_at_thirty_urls():
    # Same resolvable host repeated with distinct paths — the cap is on URL
    # count, not distinct hosts, and this avoids 50 real DNS lookups.
    urls = ",".join(f"https://x.io/{i}" for i in range(50))
    clean = _validate("ping", {"urls": urls})
    assert len(clean["urls"]) == 30


# ── loadtest ──────────────────────────────────────────────────────────


def test_loadtest_requires_url_scheme():
    with pytest.raises(ValueError, match="http"):
        _validate("loadtest", {"url": "not-a-url"})


def test_loadtest_requests_and_concurrency_clamped():
    clean = _validate("loadtest", {"url": "https://x.io", "requests": 1, "concurrency": 999})
    assert clean["requests"] == 10
    assert clean["concurrency"] == 50


# ── tls ───────────────────────────────────────────────────────────────


def test_tls_extracts_hostname_from_url():
    clean = _validate("tls", {"host": "https://zyvor.dev/some/path"})
    assert clean["host"] == "zyvor.dev"


def test_tls_rejects_host_with_slash_or_space():
    with pytest.raises(ValueError, match="hostname"):
        _validate("tls", {"host": "zyvor.dev/x"})
    with pytest.raises(ValueError, match="hostname"):
        _validate("tls", {"host": "zyvor dev"})


def test_tls_default_port_kept():
    assert _validate("tls", {"host": "zyvor.dev"})["port"] == 443


def test_tls_arbitrary_port_rejected_by_target_policy():
    # _validate's own clamp allows any port in [1, 65535], but the final
    # TargetPolicy pass (below) further restricts to the allowed port set
    # (80/443 by default) — confirms the two layers actually compose.
    from orchestrator.security.target_policy import TargetPolicyError

    with pytest.raises(TargetPolicyError, match="port"):
        _validate("tls", {"host": "zyvor.dev", "port": 8443})


# ── ai_flow ───────────────────────────────────────────────────────────


def test_ai_flow_requires_goal():
    with pytest.raises(ValueError, match="goal"):
        _validate("ai_flow", {"url": "https://x.io"})


def test_ai_flow_max_steps_clamped():
    clean = _validate("ai_flow", {"url": "https://x.io", "goal": "log in", "max_steps": 999})
    assert clean["max_steps"] == 40


# ── probe kinds ───────────────────────────────────────────────────────


def test_dns_records_requires_a_host():
    with pytest.raises(ValueError, match="hostname"):
        _validate("dns_records", {})
    clean = _validate("dns_records", {"url": "zyvor.dev"})
    assert clean["host"] == "zyvor.dev"


@pytest.mark.parametrize("kind", sorted(k for k in VALID_KINDS if k != "dns_records" and k in
                                         {"redirects", "headers", "cookies", "robots", "security_paths",
                                          "api_check", "sitemap_test", "cors", "transport"}))
def test_other_probe_kinds_require_url_scheme(kind):
    with pytest.raises(ValueError, match="http"):
        _validate(kind, {"url": "not-a-url"})
    clean = _validate(kind, {"url": "https://x.io"})
    assert clean["url"].startswith("https://x.io")


def test_api_check_extra_fields():
    clean = _validate(
        "api_check", {"url": "https://x.io/api", "expect_status": 201, "json_path": "data.id", "contains": "ok"}
    )
    assert clean["expect_status"] == 201
    assert clean["json_path"] == "data.id"
    assert clean["contains"] == "ok"


# --- Elevated-risk kinds (misconfig_scan / cve_lookup / llm_redteam) -------
# These all require a live, sufficiently-scoped security engagement
# (orchestrator/security/engagement_policy.py) — fake the store so _validate()
# doesn't need a real SQLite DB.

import orchestrator.persistence.store as _store_module  # noqa: E402


class _FakeEngagementStore:
    def __init__(self, engagement):
        self._engagement = engagement

    def get_engagement(self, engagement_id):
        return self._engagement if engagement_id == "eng-1" else None

    def audit(self, action, **kwargs):
        pass


def _allow_engagement(monkeypatch, *, target_pattern="*", tier="active_recon"):
    engagement = {
        "id": "eng-1", "target_pattern": target_pattern, "scope_statement": "authorized",
        "tier": tier, "authorized_by": "admin", "created_at": "2026-01-01T00:00:00+00:00",
        "expires_at": None, "revoked_at": None, "revoked_by": None,
    }
    monkeypatch.setattr(_store_module, "get_store", lambda: _FakeEngagementStore(engagement))


@pytest.mark.parametrize("kind", ["misconfig_scan", "cve_lookup", "llm_redteam"])
def test_elevated_kinds_registered(kind):
    assert kind in VALID_KINDS


@pytest.mark.parametrize("kind", ["misconfig_scan", "cve_lookup"])
def test_elevated_kinds_require_url_scheme(monkeypatch, kind):
    _allow_engagement(monkeypatch)
    with pytest.raises(ValueError, match="http"):
        _validate(kind, {"url": "not-a-url", "engagement_id": "eng-1"})


@pytest.mark.parametrize("kind", ["misconfig_scan", "cve_lookup", "llm_redteam"])
def test_elevated_kinds_reject_missing_engagement(monkeypatch, kind):
    monkeypatch.setattr(_store_module, "get_store", lambda: _FakeEngagementStore(None))
    params = {"url": "https://x.io"} if kind != "llm_redteam" else {}
    with pytest.raises(ValueError, match="authorized security engagement"):
        _validate(kind, params)


@pytest.mark.parametrize("kind", ["misconfig_scan", "cve_lookup"])
def test_elevated_kinds_reject_out_of_scope_target(monkeypatch, kind):
    _allow_engagement(monkeypatch, target_pattern="only-this.example.com")
    with pytest.raises(ValueError, match="outside engagement scope"):
        _validate(kind, {"url": "https://x.io", "engagement_id": "eng-1"})


def test_misconfig_scan_caps_max_paths(monkeypatch):
    _allow_engagement(monkeypatch)
    clean = _validate("misconfig_scan", {"url": "https://x.io", "max_paths": 99999, "engagement_id": "eng-1"})
    assert clean["max_paths"] == 300


def test_misconfig_scan_clean_defaults(monkeypatch):
    _allow_engagement(monkeypatch)
    clean = _validate("misconfig_scan", {"url": "https://x.io", "engagement_id": "eng-1"})
    assert clean["max_paths"] == 60
    assert clean["insecure"] is False


def test_cve_lookup_clean_defaults(monkeypatch):
    _allow_engagement(monkeypatch)
    clean = _validate("cve_lookup", {"url": "https://x.io", "engagement_id": "eng-1"})
    assert clean["url"].startswith("https://x.io")


def test_contract_verify_requires_har(monkeypatch):
    _allow_engagement(monkeypatch)
    with pytest.raises(ValueError, match="HAR"):
        _validate("contract_verify", {"url": "https://x.io", "engagement_id": "eng-1"})


def test_contract_verify_clean_defaults(monkeypatch):
    _allow_engagement(monkeypatch)
    clean = _validate("contract_verify", {"url": "https://x.io", "har": "/tmp/x.har", "engagement_id": "eng-1"})
    assert clean["har"] == "/tmp/x.har"
    assert clean["max_endpoints"] == 60


def test_contract_verify_reject_missing_engagement(monkeypatch):
    monkeypatch.setattr(_store_module, "get_store", lambda: _FakeEngagementStore(None))
    with pytest.raises(ValueError, match="authorized security engagement"):
        _validate("contract_verify", {"url": "https://x.io", "har": "/tmp/x.har"})


def test_sca_scan_requires_url_or_checkout_path():
    with pytest.raises(ValueError, match="checkout_path"):
        _validate("sca_scan", {})


def test_sca_scan_blackbox_mode_requires_engagement(monkeypatch):
    monkeypatch.setattr(_store_module, "get_store", lambda: _FakeEngagementStore(None))
    with pytest.raises(ValueError, match="authorized security engagement"):
        _validate("sca_scan", {"url": "https://x.io"})


def test_sca_scan_local_checkout_only_mode_needs_no_engagement():
    """checkout_path reads an operator-local filesystem path -- no target,
    no engagement, unlike every other kind in ELEVATED_RISK_KINDS."""
    clean = _validate("sca_scan", {"checkout_path": "/repo/checkout"})
    assert clean["checkout_path"] == "/repo/checkout"
    assert clean["url"] == ""
    assert clean["engagement_id"] is None


def test_sca_scan_both_modes_together(monkeypatch):
    _allow_engagement(monkeypatch)
    clean = _validate("sca_scan", {"url": "https://x.io", "checkout_path": "/repo", "engagement_id": "eng-1"})
    assert clean["url"].startswith("https://x.io")
    assert clean["checkout_path"] == "/repo"


# --- db_assert: 'active_recon' engagement tier PLUS a separate,
# independent ZYVOR_DB_TESTING_ENABLED opt-in (fail-closed default). Read-
# only, but touches live data with real credentials -- one gate, not
# exploit_poc's three-gate stack.

def _db_assert_params(**overrides):
    params = {
        "engine": "postgres", "target": "staging-orders-db",
        "db_secret": {"$secret": "env:DB_DSN"}, "query": "SELECT * FROM orders",
        "assertion": {"mode": "row_count", "op": "==", "value": 1}, "engagement_id": "eng-1",
    }
    params.update(overrides)
    return params


def test_db_assert_registered():
    assert "db_assert" in VALID_KINDS


def test_db_assert_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ZYVOR_DB_TESTING_ENABLED", raising=False)
    with pytest.raises(ValueError, match="ZYVOR_DB_TESTING_ENABLED"):
        _validate("db_assert", _db_assert_params())


def test_db_assert_rejects_invalid_engine(monkeypatch):
    monkeypatch.setenv("ZYVOR_DB_TESTING_ENABLED", "true")
    _allow_engagement(monkeypatch)
    with pytest.raises(ValueError, match="engine"):
        _validate("db_assert", _db_assert_params(engine="mssql"))


def test_db_assert_requires_secret_ref_not_raw_value(monkeypatch):
    monkeypatch.setenv("ZYVOR_DB_TESTING_ENABLED", "true")
    _allow_engagement(monkeypatch)
    with pytest.raises(ValueError, match="db_secret"):
        _validate("db_assert", _db_assert_params(db_secret="postgresql://user:pass@host/db"))


def test_db_assert_rejects_non_select_query(monkeypatch):
    monkeypatch.setenv("ZYVOR_DB_TESTING_ENABLED", "true")
    _allow_engagement(monkeypatch)
    with pytest.raises(ValueError, match="SELECT"):
        _validate("db_assert", _db_assert_params(query="DELETE FROM orders"))


def test_db_assert_requires_target_label(monkeypatch):
    monkeypatch.setenv("ZYVOR_DB_TESTING_ENABLED", "true")
    _allow_engagement(monkeypatch)
    with pytest.raises(ValueError, match="target"):
        _validate("db_assert", _db_assert_params(target=""))


def test_db_assert_rejects_invalid_assertion_shape(monkeypatch):
    monkeypatch.setenv("ZYVOR_DB_TESTING_ENABLED", "true")
    _allow_engagement(monkeypatch)
    with pytest.raises(ValueError, match="assertion"):
        _validate("db_assert", _db_assert_params(assertion={"mode": "bogus"}))
    with pytest.raises(ValueError, match="assertion"):
        _validate("db_assert", _db_assert_params(assertion="not a dict"))


def test_db_assert_clean_defaults(monkeypatch):
    monkeypatch.setenv("ZYVOR_DB_TESTING_ENABLED", "true")
    _allow_engagement(monkeypatch)
    clean = _validate("db_assert", _db_assert_params())
    assert clean["engine"] == "postgres"
    assert clean["target"] == "staging-orders-db"
    assert clean["db_secret"] == {"$secret": "env:DB_DSN"}
    assert clean["query"] == "SELECT * FROM orders"
    assert clean["query_params"] == []
    assert clean["timeout_s"] == 30


def test_db_assert_timeout_clamped(monkeypatch):
    monkeypatch.setenv("ZYVOR_DB_TESTING_ENABLED", "true")
    _allow_engagement(monkeypatch)
    clean = _validate("db_assert", _db_assert_params(timeout_s=9999))
    assert clean["timeout_s"] == 120


def test_db_assert_query_params_must_be_a_list(monkeypatch):
    monkeypatch.setenv("ZYVOR_DB_TESTING_ENABLED", "true")
    _allow_engagement(monkeypatch)
    clean = _validate("db_assert", _db_assert_params(query_params="not-a-list"))
    assert clean["query_params"] == []  # silently normalized, matching workflow/path_params dict-shape precedent


def test_db_assert_rejects_missing_engagement(monkeypatch):
    """Sanity check that db_assert really is gated at the engagement layer,
    independent of the ZYVOR_DB_TESTING_ENABLED opt-in above."""
    monkeypatch.setenv("ZYVOR_DB_TESTING_ENABLED", "true")
    monkeypatch.setattr(_store_module, "get_store", lambda: _FakeEngagementStore(None))
    with pytest.raises(ValueError, match="authorized security engagement"):
        _validate("db_assert", _db_assert_params(engagement_id=None))


def test_llm_redteam_dashboard_ask_needs_no_url(monkeypatch):
    _allow_engagement(monkeypatch, target_pattern="dashboard_ask")
    clean = _validate("llm_redteam", {"engagement_id": "eng-1"})
    assert clean["target"] == "dashboard_ask"
    assert clean["url"] == "dashboard_ask"
    assert clean["categories"]  # defaults to all valid categories


def test_llm_redteam_v1_qa_requires_base_url_and_api_key(monkeypatch):
    _allow_engagement(monkeypatch)
    with pytest.raises(ValueError, match="base_url"):
        _validate("llm_redteam", {"target": "v1_qa", "engagement_id": "eng-1"})
    with pytest.raises(ValueError, match="api_key"):
        _validate("llm_redteam", {"target": "v1_qa", "base_url": "https://x.io", "engagement_id": "eng-1"})


def test_llm_redteam_v1_qa_valid_params(monkeypatch):
    _allow_engagement(monkeypatch)
    clean = _validate(
        "llm_redteam",
        {"target": "v1_qa", "base_url": "https://x.io", "api_key": "k", "engagement_id": "eng-1"},
    )
    assert clean["target"] == "v1_qa"
    assert clean["url"].startswith("https://x.io")
    assert clean["api_key"] == "k"


def test_llm_redteam_invalid_target_rejected(monkeypatch):
    _allow_engagement(monkeypatch)
    with pytest.raises(ValueError, match="target"):
        _validate("llm_redteam", {"target": "not-a-real-target", "engagement_id": "eng-1"})


def test_llm_redteam_categories_filtered_to_valid_set(monkeypatch):
    _allow_engagement(monkeypatch, target_pattern="dashboard_ask")
    clean = _validate(
        "llm_redteam", {"categories": ["jailbreak", "not-a-real-category"], "engagement_id": "eng-1"}
    )
    assert clean["categories"] == ["jailbreak"]


def test_llm_redteam_max_prompts_capped(monkeypatch):
    _allow_engagement(monkeypatch, target_pattern="dashboard_ask")
    clean = _validate("llm_redteam", {"max_prompts": 9999, "engagement_id": "eng-1"})
    assert clean["max_prompts"] == 40


# --- exploit_poc: gated at the 'exploit' engagement tier PLUS a separate,
# independent ZYVOR_EXPLOIT_EXECUTION_ENABLED opt-in (fail-closed default).

def test_exploit_poc_registered():
    assert "exploit_poc" in VALID_KINDS


def test_exploit_poc_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ZYVOR_EXPLOIT_EXECUTION_ENABLED", raising=False)
    _allow_engagement(monkeypatch, tier="exploit")
    with pytest.raises(ValueError, match="ZYVOR_EXPLOIT_EXECUTION_ENABLED"):
        _validate(
            "exploit_poc",
            {"url": "https://x.io", "finding_description": "SQLi in ?id=", "engagement_id": "eng-1"},
        )


def test_exploit_poc_rejects_active_recon_tier_engagement(monkeypatch):
    monkeypatch.setenv("ZYVOR_EXPLOIT_EXECUTION_ENABLED", "true")
    _allow_engagement(monkeypatch, tier="active_recon")
    with pytest.raises(ValueError, match="insufficient"):
        _validate(
            "exploit_poc",
            {"url": "https://x.io", "finding_description": "SQLi in ?id=", "engagement_id": "eng-1"},
        )
    monkeypatch.delenv("ZYVOR_EXPLOIT_EXECUTION_ENABLED", raising=False)


def test_exploit_poc_requires_finding_description(monkeypatch):
    monkeypatch.setenv("ZYVOR_EXPLOIT_EXECUTION_ENABLED", "true")
    _allow_engagement(monkeypatch, tier="exploit")
    with pytest.raises(ValueError, match="finding_description"):
        _validate("exploit_poc", {"url": "https://x.io", "engagement_id": "eng-1"})
    monkeypatch.delenv("ZYVOR_EXPLOIT_EXECUTION_ENABLED", raising=False)


def test_exploit_poc_requires_url_scheme(monkeypatch):
    monkeypatch.setenv("ZYVOR_EXPLOIT_EXECUTION_ENABLED", "true")
    _allow_engagement(monkeypatch, tier="exploit")
    with pytest.raises(ValueError, match="http"):
        _validate("exploit_poc", {"url": "not-a-url", "finding_description": "x", "engagement_id": "eng-1"})
    monkeypatch.delenv("ZYVOR_EXPLOIT_EXECUTION_ENABLED", raising=False)


def test_exploit_poc_happy_path_with_exploit_tier_engagement(monkeypatch):
    monkeypatch.setenv("ZYVOR_EXPLOIT_EXECUTION_ENABLED", "true")
    _allow_engagement(monkeypatch, tier="exploit")
    clean = _validate(
        "exploit_poc",
        {
            "url": "https://x.io", "finding_description": "SQLi in ?id=",
            "engagement_id": "eng-1", "timeout_s": 99999,
        },
    )
    assert clean["url"].startswith("https://x.io")
    assert clean["finding_description"] == "SQLi in ?id="
    assert clean["timeout_s"] == 300  # capped
    monkeypatch.delenv("ZYVOR_EXPLOIT_EXECUTION_ENABLED", raising=False)


# --- attack_chain: same fail-closed gates as exploit_poc, plus max_steps cap.

def test_attack_chain_registered():
    assert "attack_chain" in VALID_KINDS


def test_attack_chain_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ZYVOR_EXPLOIT_EXECUTION_ENABLED", raising=False)
    _allow_engagement(monkeypatch, tier="exploit")
    with pytest.raises(ValueError, match="ZYVOR_EXPLOIT_EXECUTION_ENABLED"):
        _validate(
            "attack_chain",
            {"url": "https://x.io", "objective": "escalate SQLi to RCE", "engagement_id": "eng-1"},
        )


def test_attack_chain_rejects_active_recon_tier_engagement(monkeypatch):
    monkeypatch.setenv("ZYVOR_EXPLOIT_EXECUTION_ENABLED", "true")
    _allow_engagement(monkeypatch, tier="active_recon")
    with pytest.raises(ValueError, match="insufficient"):
        _validate(
            "attack_chain",
            {"url": "https://x.io", "objective": "escalate SQLi to RCE", "engagement_id": "eng-1"},
        )
    monkeypatch.delenv("ZYVOR_EXPLOIT_EXECUTION_ENABLED", raising=False)


def test_attack_chain_requires_objective(monkeypatch):
    monkeypatch.setenv("ZYVOR_EXPLOIT_EXECUTION_ENABLED", "true")
    _allow_engagement(monkeypatch, tier="exploit")
    with pytest.raises(ValueError, match="objective"):
        _validate("attack_chain", {"url": "https://x.io", "engagement_id": "eng-1"})
    monkeypatch.delenv("ZYVOR_EXPLOIT_EXECUTION_ENABLED", raising=False)


def test_attack_chain_max_steps_capped(monkeypatch):
    monkeypatch.setenv("ZYVOR_EXPLOIT_EXECUTION_ENABLED", "true")
    _allow_engagement(monkeypatch, tier="exploit")
    clean = _validate(
        "attack_chain",
        {"url": "https://x.io", "objective": "escalate SQLi to RCE", "max_steps": 999, "engagement_id": "eng-1"},
    )
    assert clean["max_steps"] == 5
    monkeypatch.delenv("ZYVOR_EXPLOIT_EXECUTION_ENABLED", raising=False)


# --- host_pentest / cloud_pentest: exploit-tier engagement, the same
# ZYVOR_EXPLOIT_EXECUTION_ENABLED opt-in, PLUS a second, independent
# ZYVOR_CREDENTIALED_PENTEST_ENABLED opt-in, PLUS creds must use $secret refs.

def _enable_exploit_env(monkeypatch):
    monkeypatch.setenv("ZYVOR_EXPLOIT_EXECUTION_ENABLED", "true")
    monkeypatch.setenv("ZYVOR_CREDENTIALED_PENTEST_ENABLED", "true")


def _disable_exploit_env(monkeypatch):
    monkeypatch.delenv("ZYVOR_EXPLOIT_EXECUTION_ENABLED", raising=False)
    monkeypatch.delenv("ZYVOR_CREDENTIALED_PENTEST_ENABLED", raising=False)


@pytest.mark.parametrize("kind", ["host_pentest", "cloud_pentest"])
def test_pentest_kinds_registered(kind):
    assert kind in VALID_KINDS


def test_host_pentest_requires_credentialed_opt_in_even_with_exploit_enabled(monkeypatch):
    monkeypatch.setenv("ZYVOR_EXPLOIT_EXECUTION_ENABLED", "true")
    monkeypatch.delenv("ZYVOR_CREDENTIALED_PENTEST_ENABLED", raising=False)
    _allow_engagement(monkeypatch, tier="exploit")
    with pytest.raises(ValueError, match="ZYVOR_CREDENTIALED_PENTEST_ENABLED"):
        _validate(
            "host_pentest",
            {
                "host": "zyvor.dev", "finding_description": "weak SSH config",
                "creds": {"username": "admin", "password": {"$secret": "env:X"}},
                "engagement_id": "eng-1",
            },
        )
    monkeypatch.delenv("ZYVOR_EXPLOIT_EXECUTION_ENABLED", raising=False)


def test_host_pentest_rejects_raw_password_in_creds(monkeypatch):
    _enable_exploit_env(monkeypatch)
    _allow_engagement(monkeypatch, tier="exploit")
    with pytest.raises(ValueError, match="secret"):
        _validate(
            "host_pentest",
            {
                "host": "zyvor.dev", "finding_description": "weak SSH config",
                "creds": {"username": "admin", "password": "hunter2"},  # raw, not a $secret ref
                "engagement_id": "eng-1",
            },
        )
    _disable_exploit_env(monkeypatch)


def test_host_pentest_requires_username(monkeypatch):
    _enable_exploit_env(monkeypatch)
    _allow_engagement(monkeypatch, tier="exploit")
    with pytest.raises(ValueError, match="username"):
        _validate(
            "host_pentest",
            {
                "host": "zyvor.dev", "finding_description": "x",
                "creds": {"password": {"$secret": "env:X"}},
                "engagement_id": "eng-1",
            },
        )
    _disable_exploit_env(monkeypatch)


def test_host_pentest_requires_password_or_private_key(monkeypatch):
    _enable_exploit_env(monkeypatch)
    _allow_engagement(monkeypatch, tier="exploit")
    with pytest.raises(ValueError, match="password.*private_key|private_key.*password"):
        _validate(
            "host_pentest",
            {
                "host": "zyvor.dev", "finding_description": "x",
                "creds": {"username": "admin"},
                "engagement_id": "eng-1",
            },
        )
    _disable_exploit_env(monkeypatch)


def test_host_pentest_happy_path(monkeypatch):
    _enable_exploit_env(monkeypatch)
    _allow_engagement(monkeypatch, tier="exploit", target_pattern="*.dev")
    clean = _validate(
        "host_pentest",
        {
            "host": "zyvor.dev", "port": 2222,
            "finding_description": "weak SSH config",
            "creds": {"username": "admin", "password": {"$secret": "env:SSH_PW"}},
            "engagement_id": "eng-1",
        },
    )
    assert clean["host"] == "zyvor.dev"
    assert clean["port"] == 2222
    assert clean["creds"]["password"] == {"$secret": "env:SSH_PW"}
    _disable_exploit_env(monkeypatch)


def test_cloud_pentest_rejects_invalid_provider(monkeypatch):
    _enable_exploit_env(monkeypatch)
    _allow_engagement(monkeypatch, tier="exploit")
    with pytest.raises(ValueError, match="provider"):
        _validate(
            "cloud_pentest",
            {
                "provider": "not-a-real-provider", "target": "acct-123",
                "finding_description": "x", "creds": {"api_key": {"$secret": "env:X"}},
                "engagement_id": "eng-1",
            },
        )
    _disable_exploit_env(monkeypatch)


def test_cloud_pentest_rejects_raw_secret_in_creds(monkeypatch):
    _enable_exploit_env(monkeypatch)
    _allow_engagement(monkeypatch, tier="exploit")
    with pytest.raises(ValueError, match="secret"):
        _validate(
            "cloud_pentest",
            {
                "provider": "aws", "target": "acct-123", "finding_description": "x",
                "creds": {"secret_access_key": "raw-value-not-a-ref"},
                "engagement_id": "eng-1",
            },
        )
    _disable_exploit_env(monkeypatch)


def test_cloud_pentest_happy_path(monkeypatch):
    _enable_exploit_env(monkeypatch)
    _allow_engagement(monkeypatch, tier="exploit", target_pattern="*")
    clean = _validate(
        "cloud_pentest",
        {
            "provider": "aws", "target": "aws-prod-123456789012",
            "finding_description": "overly permissive S3 bucket policy",
            "creds": {
                "access_key_id": "AKIA...",
                "secret_access_key": {"$secret": "env:AWS_SECRET"},
            },
            "engagement_id": "eng-1",
        },
    )
    assert clean["provider"] == "aws"
    assert clean["target"] == "aws-prod-123456789012"
    _disable_exploit_env(monkeypatch)


# --- chaos_inject / chaos_webhook: 'exploit'-tier engagement PLUS a
# separate ZYVOR_CHAOS_INJECTION_ENABLED opt-in PLUS a per-run
# target_accepts_fault_injection attestation (three gates total).

def _base_chaos_params(**overrides):
    params = {
        "url": "https://x.io", "target_accepts_fault_injection": True,
        "control_kind": "flow", "control_params": {"description": "assert \"x\" is visible"},
        "engagement_id": "eng-1",
    }
    params.update(overrides)
    return params


def test_chaos_kinds_registered():
    assert "chaos_inject" in VALID_KINDS
    assert "chaos_webhook" in VALID_KINDS


def test_chaos_inject_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ZYVOR_CHAOS_INJECTION_ENABLED", raising=False)
    with pytest.raises(ValueError, match="ZYVOR_CHAOS_INJECTION_ENABLED"):
        _validate("chaos_inject", _base_chaos_params(fault_type="latency"))


def test_chaos_webhook_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ZYVOR_CHAOS_INJECTION_ENABLED", raising=False)
    with pytest.raises(ValueError, match="ZYVOR_CHAOS_INJECTION_ENABLED"):
        _validate("chaos_webhook", _base_chaos_params(experiment_webhook_url="https://api.x.io/start"))


def test_chaos_inject_requires_target_attestation(monkeypatch):
    monkeypatch.setenv("ZYVOR_CHAOS_INJECTION_ENABLED", "true")
    with pytest.raises(ValueError, match="target_accepts_fault_injection"):
        _validate("chaos_inject", _base_chaos_params(fault_type="latency", target_accepts_fault_injection=False))
    with pytest.raises(ValueError, match="target_accepts_fault_injection"):
        _validate("chaos_inject", {k: v for k, v in _base_chaos_params(fault_type="latency").items()
                                    if k != "target_accepts_fault_injection"})


def test_chaos_inject_rejects_invalid_fault_type(monkeypatch):
    monkeypatch.setenv("ZYVOR_CHAOS_INJECTION_ENABLED", "true")
    _allow_engagement(monkeypatch, tier="exploit")
    with pytest.raises(ValueError, match="fault_type"):
        _validate("chaos_inject", _base_chaos_params(fault_type="bogus"))


def test_chaos_inject_rejects_disallowed_control_kind(monkeypatch):
    monkeypatch.setenv("ZYVOR_CHAOS_INJECTION_ENABLED", "true")
    _allow_engagement(monkeypatch, tier="exploit")
    with pytest.raises(ValueError, match="control_kind"):
        _validate("chaos_inject", _base_chaos_params(fault_type="latency", control_kind="exploit_poc", control_params={}))


def test_chaos_inject_rejects_active_recon_tier_engagement(monkeypatch):
    monkeypatch.setenv("ZYVOR_CHAOS_INJECTION_ENABLED", "true")
    _allow_engagement(monkeypatch, tier="active_recon")
    with pytest.raises(ValueError, match="insufficient"):
        _validate("chaos_inject", _base_chaos_params(fault_type="latency"))


def test_chaos_inject_caps_are_enforced(monkeypatch):
    monkeypatch.setenv("ZYVOR_CHAOS_INJECTION_ENABLED", "true")
    _allow_engagement(monkeypatch, tier="exploit")
    clean = _validate("chaos_inject", _base_chaos_params(
        fault_type="latency", latency_ms=99999, packet_loss_pct=999, duration_s=99999,
    ))
    assert clean["latency_ms"] == 5000
    assert clean["packet_loss_pct"] == 100
    assert clean["duration_s"] == 120


def test_chaos_inject_clean_defaults(monkeypatch):
    monkeypatch.setenv("ZYVOR_CHAOS_INJECTION_ENABLED", "true")
    _allow_engagement(monkeypatch, tier="exploit")
    clean = _validate("chaos_inject", _base_chaos_params(fault_type="latency"))
    assert clean["fault_type"] == "latency"
    assert clean["control_kind"] == "flow"
    assert clean["control_params"]["url"].startswith("https://x.io")  # url injected into control_params
    assert clean["error_rate_threshold_pct"] == 10.0
    assert clean["recovery_sla_s"] == 30.0


def test_chaos_webhook_requires_experiment_webhook_url(monkeypatch):
    monkeypatch.setenv("ZYVOR_CHAOS_INJECTION_ENABLED", "true")
    _allow_engagement(monkeypatch, tier="exploit")
    with pytest.raises(ValueError, match="experiment_webhook_url"):
        _validate("chaos_webhook", _base_chaos_params())


def test_chaos_webhook_rejects_ssrf_target_for_experiment_url(monkeypatch):
    monkeypatch.setenv("ZYVOR_CHAOS_INJECTION_ENABLED", "true")
    _allow_engagement(monkeypatch, tier="exploit")
    with pytest.raises(ValueError):
        _validate("chaos_webhook", _base_chaos_params(experiment_webhook_url="http://169.254.169.254/start"))


def test_chaos_webhook_clean_defaults(monkeypatch):
    monkeypatch.setenv("ZYVOR_CHAOS_INJECTION_ENABLED", "true")
    _allow_engagement(monkeypatch, tier="exploit")
    clean = _validate("chaos_webhook", _base_chaos_params(
        experiment_webhook_url="https://api.x.io/start", experiment_stop_webhook_url="https://api.x.io/stop",
    ))
    assert clean["experiment_webhook_url"] == "https://api.x.io/start"
    assert clean["experiment_stop_webhook_url"] == "https://api.x.io/stop"
    assert clean["settle_s"] == 5


# --- Network-attack / DAST kinds -------------------------------------------------

@pytest.mark.parametrize(
    "kind",
    [
        "port_scan", "tls_cipher_scan", "dast_scan", "injection_scan",
        "csrf_probe", "ssrf_probe", "auth_attack_scan", "idor_scan",
    ],
)
def test_network_attack_kinds_registered(kind):
    assert kind in VALID_KINDS


def test_port_scan_active_recon_happy(monkeypatch):
    _allow_engagement(monkeypatch, tier="active_recon")
    clean = _validate("port_scan", {"url": "https://x.io", "engagement_id": "eng-1", "ports": "22,80,443"})
    assert clean["ports"] == [22, 80, 443]
    assert clean["url"].startswith("https://x.io")


def test_port_scan_rejects_exploit_only_when_missing_engagement(monkeypatch):
    monkeypatch.setattr(_store_module, "get_store", lambda: _FakeEngagementStore(None))
    with pytest.raises(ValueError):
        _validate("port_scan", {"url": "https://x.io"})


def test_tls_cipher_scan_happy(monkeypatch):
    _allow_engagement(monkeypatch, tier="active_recon")
    clean = _validate("tls_cipher_scan", {"url": "https://x.io", "engagement_id": "eng-1", "port": 8443})
    assert clean["port"] == 8443


@pytest.mark.parametrize(
    "kind",
    ["dast_scan", "injection_scan", "csrf_probe", "ssrf_probe", "auth_attack_scan", "idor_scan"],
)
def test_dast_kinds_disabled_by_default(monkeypatch, kind):
    monkeypatch.delenv("ZYVOR_DAST_SCAN_ENABLED", raising=False)
    _allow_engagement(monkeypatch, tier="exploit")
    with pytest.raises(ValueError, match="ZYVOR_DAST_SCAN_ENABLED"):
        _validate(kind, {"url": "https://x.io", "engagement_id": "eng-1"})


@pytest.mark.parametrize(
    "kind",
    ["dast_scan", "injection_scan", "csrf_probe", "ssrf_probe", "auth_attack_scan", "idor_scan"],
)
def test_dast_kinds_reject_active_recon_tier(monkeypatch, kind):
    monkeypatch.setenv("ZYVOR_DAST_SCAN_ENABLED", "true")
    _allow_engagement(monkeypatch, tier="active_recon")
    with pytest.raises(ValueError, match="insufficient"):
        _validate(kind, {"url": "https://x.io", "engagement_id": "eng-1"})
    monkeypatch.delenv("ZYVOR_DAST_SCAN_ENABLED", raising=False)


def test_dast_scan_happy_path(monkeypatch):
    monkeypatch.setenv("ZYVOR_DAST_SCAN_ENABLED", "true")
    _allow_engagement(monkeypatch, tier="exploit")
    clean = _validate(
        "dast_scan",
        {
            "url": "https://x.io",
            "engagement_id": "eng-1",
            "modules": "headers,injection",
            "max_requests": 999,
        },
    )
    assert clean["modules"] == ["headers", "injection"]
    assert clean["max_requests"] == 80  # capped
    monkeypatch.delenv("ZYVOR_DAST_SCAN_ENABLED", raising=False)


def test_idor_scan_accepts_cookie(monkeypatch):
    monkeypatch.setenv("ZYVOR_DAST_SCAN_ENABLED", "true")
    _allow_engagement(monkeypatch, tier="exploit")
    clean = _validate(
        "idor_scan",
        {"url": "https://x.io/orders/1", "engagement_id": "eng-1", "cookie": "sid=abc", "delta": 9},
    )
    assert clean["cookie"] == "sid=abc"
    assert clean["delta"] == 5  # capped
    monkeypatch.delenv("ZYVOR_DAST_SCAN_ENABLED", raising=False)
