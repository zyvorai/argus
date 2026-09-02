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

"""Unit tests for agents/sca/engine.py -- dependency/license scanning of the
target app (black-box client-side fingerprinting + local-checkout mode)."""

from __future__ import annotations

import json
import subprocess

import agents.sca.engine as sca_engine
from agents.sca.engine import _detect_ecosystem, scan_blackbox, scan_local_checkout


def test_license_map_loads_real_bundled_file():
    license_map = sca_engine._license_map()
    assert license_map["jquery"] == "MIT"
    assert "_comment" not in license_map  # metadata key filtered out


def test_scan_blackbox_flags_non_permissive_license(monkeypatch):
    import agents.probes.misconfig_scan as misconfig_scan_module

    monkeypatch.setattr(misconfig_scan_module, "fingerprint_tech", lambda url, insecure=False: {
        "versions": [{"product": "WordPress", "version": "6.4", "source": "meta:generator"}],
    })
    result = scan_blackbox("https://x.io")
    lib = result["libraries"][0]
    assert lib["license"] == "GPL-2.0-or-later"
    assert lib["risk"] == "copyleft-or-restricted"


def test_scan_blackbox_permissive_license_has_no_risk(monkeypatch):
    import agents.probes.misconfig_scan as misconfig_scan_module

    monkeypatch.setattr(misconfig_scan_module, "fingerprint_tech", lambda url, insecure=False: {
        "versions": [{"product": "jQuery", "version": "3.4.1", "source": "asset:jquery"}],
    })
    result = scan_blackbox("https://x.io")
    assert result["libraries"][0]["risk"] is None


def test_scan_blackbox_unknown_product_flagged_unknown(monkeypatch):
    import agents.probes.misconfig_scan as misconfig_scan_module

    monkeypatch.setattr(misconfig_scan_module, "fingerprint_tech", lambda url, insecure=False: {
        "versions": [{"product": "SomeInternalTool", "version": "1.0", "source": "header:server"}],
    })
    result = scan_blackbox("https://x.io")
    assert result["libraries"][0]["risk"] == "unknown"
    assert result["libraries"][0]["license"] is None


# -- local-checkout mode ----------------------------------------------------

def test_detect_ecosystem_python_requirements_txt(tmp_path):
    (tmp_path / "requirements.txt").write_text("requests\n")
    assert _detect_ecosystem(tmp_path) == "python"


def test_detect_ecosystem_python_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    assert _detect_ecosystem(tmp_path) == "python"


def test_detect_ecosystem_npm(tmp_path):
    (tmp_path / "package.json").write_text("{}")
    assert _detect_ecosystem(tmp_path) == "npm"


def test_detect_ecosystem_none(tmp_path):
    assert _detect_ecosystem(tmp_path) is None


def test_scan_local_checkout_not_a_directory():
    result = scan_local_checkout("/does/not/exist")
    assert result["skipped"] is True
    assert "not a directory" in result["reason"]


def test_scan_local_checkout_no_manifest(tmp_path):
    result = scan_local_checkout(str(tmp_path))
    assert result["skipped"] is True
    assert "no requirements.txt" in result["reason"]


def test_scan_local_checkout_tool_not_found_degrades_gracefully(tmp_path, monkeypatch):
    (tmp_path / "requirements.txt").write_text("requests\n")
    monkeypatch.setattr(sca_engine.shutil, "which", lambda name: None)
    result = scan_local_checkout(str(tmp_path))
    assert result["skipped"] is True
    assert "pip-audit not found" in result["reason"]


def test_scan_local_checkout_uses_dash_r_for_requirements_txt(tmp_path, monkeypatch):
    """A real bug caught in live verification: without -r/a project path,
    pip-audit silently audits the *running* Python environment instead of
    the checkout -- this locks in the fix."""
    (tmp_path / "requirements.txt").write_text("requests==2.19.1\n")
    monkeypatch.setattr(sca_engine.shutil, "which", lambda name: "/usr/bin/pip-audit")
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout='{"dependencies": []}', stderr="")

    monkeypatch.setattr(sca_engine.subprocess, "run", fake_run)
    scan_local_checkout(str(tmp_path))
    assert "-r" in captured["cmd"]
    assert "requirements.txt" in captured["cmd"]


def test_scan_local_checkout_normalizes_pip_audit_vulnerabilities(tmp_path, monkeypatch):
    (tmp_path / "requirements.txt").write_text("requests==2.19.1\n")
    monkeypatch.setattr(sca_engine.shutil, "which", lambda name: "/usr/bin/pip-audit")
    payload = {
        "dependencies": [{"name": "requests", "version": "2.19.1", "vulns": [
            {"id": "PYSEC-2018-28", "description": "leaks credentials"},
        ]}],
    }

    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(sca_engine.subprocess, "run", fake_run)
    result = scan_local_checkout(str(tmp_path))
    assert result["skipped"] is False
    assert result["vulnerabilities"] == [
        {"product": "requests", "version": "2.19.1", "id": "PYSEC-2018-28",
         "detail": "leaks credentials", "severity": "medium"},
    ]


def test_scan_local_checkout_handles_non_json_tool_output(tmp_path, monkeypatch):
    (tmp_path / "requirements.txt").write_text("requests\n")
    monkeypatch.setattr(sca_engine.shutil, "which", lambda name: "/usr/bin/pip-audit")
    monkeypatch.setattr(sca_engine.subprocess, "run",
                         lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, stdout="not json", stderr="boom"))
    result = scan_local_checkout(str(tmp_path))
    assert result["skipped"] is True
    assert "non-JSON" in result["reason"]


def test_scan_local_checkout_npm_normalizes_vulnerabilities(tmp_path, monkeypatch):
    (tmp_path / "package.json").write_text("{}")
    monkeypatch.setattr(sca_engine.shutil, "which", lambda name: "/usr/bin/npm")
    payload = {"vulnerabilities": {"lodash": {
        "severity": "high", "range": "<4.17.21",
        "via": [{"source": 1234, "title": "Prototype Pollution"}],
    }}}

    def fake_run(cmd, **kwargs):
        assert "audit" in cmd
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(sca_engine.subprocess, "run", fake_run)
    result = scan_local_checkout(str(tmp_path))
    assert result["vulnerabilities"][0]["product"] == "lodash"
    assert result["vulnerabilities"][0]["severity"] == "high"
    assert "Prototype Pollution" in result["vulnerabilities"][0]["detail"]
