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

"""Optional OpenTelemetry distributed tracing.

Opt-in via ZYVOR_OTEL_ENABLED=true -- matching this codebase's existing
explicit-flag convention (ENABLE_AUTOFIX, ZYVOR_EXPLOIT_EXECUTION_ENABLED,
...) rather than auto-enabling just because the `otel` extra happens to be
installed. Without the extra installed, or with tracing disabled, start_span()
is a safe no-op context manager (yields None) -- callers never need to branch
on whether tracing is actually configured, the same "dependency-free by
default" posture as observability/metrics.py.

Exporter: OTLP/HTTP to OTEL_EXPORTER_OTLP_ENDPOINT if set, otherwise spans
print to stdout via OpenTelemetry's own ConsoleSpanExporter -- genuine SDK
behavior, not a stub, useful for local debugging without a collector.

Cross-replica propagation: `current_traceparent()` serializes the active
span's context as a W3C `traceparent` string, persisted on the `jobs` row
(both MissionControlStore and PostgresStore) at enqueue time; `start_span`'s
`trace_context` argument extracts it back out when the worker claims the
job, so `job.enqueue` and `job.execute` link into one trace even when they
run on different replicas -- instead of two independent ones.
"""

from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from typing import Any, Iterator

_tracer: Any = None
_tracer_lock = threading.Lock()


def tracing_enabled() -> bool:
    return os.environ.get("ZYVOR_OTEL_ENABLED", "false").lower() == "true"


def _get_tracer() -> Any:
    """Returns an OTel tracer, or False (sentinel for "not available/enabled").
    Cached after first call -- mirrors observability/metrics.py's module-level
    state, and matches the once-per-process SDK/provider setup OTel expects."""
    global _tracer
    if _tracer is not None:
        return _tracer
    with _tracer_lock:
        if _tracer is not None:
            return _tracer
        if not tracing_enabled():
            _tracer = False
            return _tracer
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import (
                BatchSpanProcessor,
                ConsoleSpanExporter,
                SimpleSpanProcessor,
            )

            provider = TracerProvider(resource=Resource.create({"service.name": "zyvor-argus"}))
            endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
            if endpoint:
                from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

                provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
            else:
                provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
            trace.set_tracer_provider(provider)
            _tracer = trace.get_tracer("zyvor-argus")
        except ImportError:
            _tracer = False
        return _tracer


def current_traceparent() -> str | None:
    """Serializes the active span's context as a W3C `traceparent` string, for
    persisting alongside a job so `job.execute` -- possibly claimed on a
    different replica -- can link into the same trace as the `job.enqueue`
    span that created it. None when tracing is disabled/unavailable, or when
    called outside any active span (nothing valid to serialize)."""
    tracer = _get_tracer()
    if not tracer:
        return None
    from opentelemetry import trace
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

    if not trace.get_current_span().get_span_context().is_valid:
        return None
    carrier: dict[str, str] = {}
    TraceContextTextMapPropagator().inject(carrier)
    return carrier.get("traceparent")


@contextmanager
def start_span(name: str, *, trace_context: str | None = None, **attributes: Any) -> Iterator[Any]:
    """`with start_span("job.execute", job_id=..., job_kind=...) as span:` --
    `span` is None when tracing is disabled/unavailable; callers that want to
    set additional attributes conditionally should guard with `if span:`.

    `trace_context` -- a `traceparent` string from `current_traceparent()`,
    e.g. read back off a claimed job row -- makes the new span a child of
    that remote context instead of whatever's locally active, the mechanism
    that links a `job.execute` span to its `job.enqueue` span across
    replicas. Omitted or None: behaves exactly as before, parented to
    whatever's currently active in this process (or a new root span)."""
    tracer = _get_tracer()
    if not tracer:
        yield None
        return
    parent_context = None
    if trace_context:
        from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

        parent_context = TraceContextTextMapPropagator().extract({"traceparent": trace_context})
    with tracer.start_as_current_span(name, context=parent_context) as span:
        for key, value in attributes.items():
            if value is not None:
                span.set_attribute(key, value)
        yield span


def set_span_error(span: Any, error: str) -> None:
    if span is None:
        return
    from opentelemetry.trace import Status, StatusCode

    span.set_status(Status(StatusCode.ERROR, str(error)[:500]))
    span.set_attribute("error", True)
