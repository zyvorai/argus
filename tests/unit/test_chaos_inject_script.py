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

"""Unit tests for agents/chaos/inject_script.py -- the mechanical (not
LLM-generated) tc/iptables fault-injection script builder.

Two of these tests actually execute the generated script's *control flow*
(trap/background/wait structure) as a real subprocess, with the real
tc/iptables command text swapped for a harmless no-op -- this locks in two
real bugs caught during development: (1) a bare foreground `sleep` is not
interruptible by a trap in `sh`, so an early kill signal would silently
wait out the full sleep duration before tearing anything down; (2) the
trap firing does not by itself stop an already-backgrounded sibling
process, so the sleep child was left orphaned. Real tc/iptables commands
are never executed anywhere in this test file -- only shell syntax
checking (`sh -n`) and a harmless-substitution control-flow run."""

from __future__ import annotations

import subprocess

import pytest

from agents.chaos.inject_script import FAULT_TYPES, InjectScriptError, build_injection_script


def _base_kwargs(**overrides):
    kwargs = {
        "fault_type": "latency", "target_host": "10.0.0.5", "target_port": 443,
        "latency_ms": 200, "packet_loss_pct": 10, "duration_s": 30,
    }
    kwargs.update(overrides)
    return kwargs


def test_rejects_unsupported_fault_type():
    with pytest.raises(InjectScriptError, match="unsupported fault_type"):
        build_injection_script(**_base_kwargs(fault_type="bogus"))


@pytest.mark.parametrize("fault_type", FAULT_TYPES)
def test_generates_syntactically_valid_shell_for_every_fault_type(tmp_path, fault_type):
    script = build_injection_script(**_base_kwargs(fault_type=fault_type))
    script_path = tmp_path / "inject.sh"
    script_path.write_text(script)
    proc = subprocess.run(["sh", "-n", str(script_path)], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr


def test_latency_uses_tc_netem_delay():
    script = build_injection_script(**_base_kwargs(fault_type="latency", latency_ms=250))
    assert "tc qdisc add dev eth0 root netem delay 250ms" in script
    assert "tc qdisc del dev eth0 root" in script  # teardown


def test_packet_loss_uses_tc_netem_loss():
    script = build_injection_script(**_base_kwargs(fault_type="packet_loss", packet_loss_pct=15))
    assert "tc qdisc add dev eth0 root netem loss 15%" in script


def test_connection_reset_uses_iptables_reject_scoped_to_target():
    script = build_injection_script(**_base_kwargs(fault_type="connection_reset", target_host="10.1.2.3", target_port=8080))
    assert "iptables -A OUTPUT -p tcp -d 10.1.2.3 --dport 8080 -j REJECT --reject-with tcp-reset" in script
    assert "iptables -D OUTPUT -p tcp -d 10.1.2.3 --dport 8080 -j REJECT --reject-with tcp-reset" in script


def test_dependency_timeout_uses_iptables_drop_scoped_to_target():
    script = build_injection_script(**_base_kwargs(fault_type="dependency_timeout", target_host="10.1.2.3", target_port=8080))
    assert "iptables -A OUTPUT -p tcp -d 10.1.2.3 --dport 8080 -j DROP" in script
    assert "iptables -D OUTPUT -p tcp -d 10.1.2.3 --dport 8080 -j DROP" in script


def test_teardown_fires_promptly_on_early_kill_not_after_full_duration(tmp_path):
    """Regression test for the sleep/trap interruptibility bug found during
    development. Runs the REAL generated script with the tc command swapped
    for a harmless no-op, kills it after 1s (against a 30s duration), and
    asserts it tears down almost immediately rather than hanging for the
    full 30s."""
    import os
    import signal
    import time

    script = build_injection_script(**_base_kwargs(fault_type="latency", duration_s=30))
    script = script.replace("tc qdisc add dev eth0 root netem delay 200ms", "true")
    script = script.replace("tc qdisc del dev eth0 root", "true")
    script_path = tmp_path / "inject.sh"
    script_path.write_text(script)

    proc = subprocess.Popen(["sh", str(script_path)], stdout=subprocess.PIPE, text=True)
    time.sleep(1)
    t0 = time.monotonic()
    os.kill(proc.pid, signal.SIGTERM)
    out = ""
    try:
        out, _ = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        pytest.fail("script did not tear down within 5s of SIGTERM (waited out the sleep instead)")
    elapsed = time.monotonic() - t0

    assert elapsed < 5, f"teardown took {elapsed:.1f}s, expected near-immediate"
    assert out.count('"phase": "teardown_complete"') == 1  # exactly once, not once per trapped signal
    assert '"phase": "fault_applied"' in out


def test_teardown_also_fires_on_normal_completion(tmp_path):
    script = build_injection_script(**_base_kwargs(fault_type="latency", duration_s=1))
    script = script.replace("tc qdisc add dev eth0 root netem delay 200ms", "true")
    script = script.replace("tc qdisc del dev eth0 root", "true")
    script_path = tmp_path / "inject.sh"
    script_path.write_text(script)

    proc = subprocess.run(["sh", str(script_path)], capture_output=True, text=True, timeout=10)
    assert proc.returncode == 0
    assert '"phase": "teardown_complete"' in proc.stdout
