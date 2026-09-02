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

"""Unit tests for agents/chaos/probe.py -- latency/recovery measurement.
Plain HTTP timing, no privileged operations, so this is live-tested against
a real local HTTP server (unlike the tc/iptables fault-injection mechanism
itself, which is unit-tested only -- see ROADMAP.md)."""

from __future__ import annotations

import http.server
import threading
import time

import pytest

from agents.chaos.probe import measure_latency_s, measure_recovery_s


@pytest.fixture()
def slow_then_fast_server():
    """A real local server: slow (0.5s) for the first `slow_until_s`
    seconds after the fixture starts, then fast -- lets tests measure a
    genuine recovery window, not just an already-fast trivial case."""
    start = time.monotonic()
    slow_until_s = 2.0

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if time.monotonic() - start < slow_until_s:
                time.sleep(0.5)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, *a):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}/", slow_until_s
    finally:
        server.shutdown()


def test_measure_latency_against_a_real_server(slow_then_fast_server):
    url, _ = slow_then_fast_server
    latency = measure_latency_s(url)
    assert latency is not None
    assert latency > 0


def test_measure_latency_returns_none_on_connection_failure():
    latency = measure_latency_s("http://127.0.0.1:1/", timeout_s=1)
    assert latency is None


def test_measure_recovery_detects_a_real_recovery_window(slow_then_fast_server):
    url, slow_until_s = slow_then_fast_server
    recovery = measure_recovery_s(url, baseline_s=0.05, tolerance_factor=2.0, max_wait_s=6, poll_interval_s=0.3)
    assert recovery is not None
    # started measuring immediately; server becomes fast at slow_until_s --
    # real recovery time should land somewhere in a believable window, not
    # near-zero (which would mean the "slow" phase wasn't really measured).
    assert 0.5 < recovery < slow_until_s + 2


def test_measure_recovery_returns_none_when_it_never_recovers():
    recovery = measure_recovery_s(
        "http://127.0.0.1:1/", baseline_s=0.05, tolerance_factor=1.5, max_wait_s=2, poll_interval_s=0.5,
    )
    assert recovery is None


def test_measure_recovery_fast_path_when_already_recovered(slow_then_fast_server):
    url, slow_until_s = slow_then_fast_server
    time.sleep(slow_until_s + 0.5)  # wait until the server is already fast
    recovery = measure_recovery_s(url, baseline_s=0.05, tolerance_factor=3.0, max_wait_s=5, poll_interval_s=0.2)
    assert recovery is not None
    assert recovery < 1.0
