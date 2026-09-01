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

"""Mission Control proxy for the Zyvor knowledge QA agent."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel, Field, field_validator

LOGGER = logging.getLogger(__name__)

router = APIRouter()

SUGGESTIONS = [
    {
        "question": "How can PacketWolf allow namespace communication while blocking internet access?",
        "product": "PacketWolf",
    },
    {
        "question": "How do I migrate a VMware VM to KubeVirt with HyperSDK?",
        "product": "HyperSDK",
    },
    {
        "question": "Why might Hubble Relay time out after 15000ms in PacketWolf?",
        "product": "PacketWolf",
    },
    {
        "question": "What GuestKit checks should I run before converting a VMDK?",
        "product": "GuestKit",
    },
    {
        "question": "Which Zeus OS components are required for KubeVirt live migration?",
        "product": "Zeus OS",
    },
    {
        "question": "How do I verify default-deny egress while allowing DNS?",
        "product": "PacketWolf",
    },
    {
        "question": "Is Hubble Relay healthy, and what does the known-issue doc say about timeouts?",
        "product": "PacketWolf",
    },
    {
        "question": "Summarise pods and deployments in the allowed namespace (read-only).",
        "product": None,
    },
]


class AskBody(BaseModel):
    question: str = Field(min_length=2)
    thread_id: str | None = Field(default=None, max_length=200)
    product: str | None = Field(default=None, max_length=100)
    document_type: str | None = Field(default=None, max_length=100)

    @field_validator("question")
    @classmethod
    def clean_question(cls, value: str) -> str:
        return " ".join(value.strip().split())


class RemediationBody(BaseModel):
    issue: str = Field(min_length=2, max_length=4000)
    thread_id: str | None = Field(default=None, max_length=200)

    @field_validator("issue")
    @classmethod
    def clean_issue(cls, value: str) -> str:
        return " ".join(value.strip().split())


class RemediationResumeBody(BaseModel):
    thread_id: str = Field(min_length=2, max_length=200)
    decision: str = Field(default="approve")
    message: str | None = Field(default=None, max_length=1000)

    @field_validator("decision")
    @classmethod
    def clean_decision(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"approve", "reject"}:
            raise ValueError("decision must be approve or reject")
        return cleaned


def _knowledge_unavailable(detail: str, status_code: int = 501) -> JSONResponse:
    return JSONResponse({"detail": detail, "available": False}, status_code=status_code)


@router.get("/api/dashboard/knowledge/status")
def knowledge_status() -> dict[str, Any]:
    from knowledge import knowledge_configured, knowledge_deps_available

    deps = knowledge_deps_available()
    configured = knowledge_configured()
    qdrant = "unknown"
    status = "offline"
    live_tools = False
    live_namespaces: list[str] = []
    remediation = False
    streaming = True

    if not deps:
        return {
            "status": "offline",
            "available": False,
            "deps_installed": False,
            "configured": False,
            "qdrant": "n/a",
            "live_tools": False,
            "live_namespaces": [],
            "remediation": False,
            "streaming": False,
            "detail": "Install optional extras: pip install -e '.[knowledge]'",
        }

    try:
        from knowledge.config import get_settings

        settings = get_settings()
        live_tools = bool(settings.enable_live_cluster_tools)
        remediation = bool(settings.enable_remediation_agent)
        streaming = bool(settings.enable_ask_streaming)
        if live_tools:
            from knowledge.cluster import allowed_namespaces

            live_namespaces = list(allowed_namespaces())
    except Exception:
        remediation = False
        streaming = True

    if not configured:
        return {
            "status": "degraded",
            "available": False,
            "deps_installed": True,
            "configured": False,
            "qdrant": "unknown",
            "live_tools": live_tools,
            "live_namespaces": live_namespaces,
            "remediation": remediation,
            "streaming": streaming,
            "detail": "Set LLM_API_KEY (and start Qdrant) to enable Ask Zyra",
        }

    try:
        from knowledge.vectorstore import get_qdrant_client

        get_qdrant_client().get_collections()
        qdrant = "reachable"
        status = "ok"
    except Exception as exc:
        LOGGER.warning("Knowledge status Qdrant check failed: %s", exc)
        qdrant = "unreachable"
        status = "degraded"

    return {
        "status": status,
        "available": status == "ok",
        "deps_installed": True,
        "configured": True,
        "qdrant": qdrant,
        "live_tools": live_tools,
        "live_namespaces": live_namespaces,
        "remediation": remediation,
        "streaming": streaming,
        "detail": None if status == "ok" else "Qdrant is unreachable",
    }


@router.get("/api/dashboard/knowledge/suggestions")
def knowledge_suggestions() -> dict[str, Any]:
    return {"suggestions": SUGGESTIONS}


@router.post("/api/dashboard/remediation")
def dashboard_remediation(body: RemediationBody) -> dict[str, Any]:
    """Session-auth proxy to the separate remediation planner (disabled by default)."""
    from knowledge.remediation import plan_remediation, remediation_enabled

    if not remediation_enabled():
        return {
            "enabled": False,
            "detail": "Set ENABLE_REMEDIATION_AGENT=true to enable the HITL remediation planner.",
        }
    try:
        return plan_remediation(issue=body.issue, thread_id=body.thread_id)
    except Exception as exc:
        LOGGER.exception("Dashboard remediation failed")
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/api/dashboard/remediation/resume")
def dashboard_remediation_resume(body: RemediationResumeBody) -> dict[str, Any]:
    from knowledge.remediation import remediation_enabled, resume_remediation

    if not remediation_enabled():
        return {
            "enabled": False,
            "detail": "Set ENABLE_REMEDIATION_AGENT=true to enable the HITL remediation planner.",
        }
    try:
        return resume_remediation(
            thread_id=body.thread_id,
            decision=body.decision,  # type: ignore[arg-type]
            message=body.message,
        )
    except Exception as exc:
        LOGGER.exception("Dashboard remediation resume failed")
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/api/dashboard/ask/stream")
def dashboard_ask_stream(body: AskBody) -> Response:
    """SSE progress stream for Ask Zyra (POST body; fetch ReadableStream in the UI)."""
    import json

    from knowledge import knowledge_configured, knowledge_deps_available

    if not knowledge_deps_available():
        return _knowledge_unavailable(
            "Knowledge agent extras are not installed.",
            status_code=501,
        )
    if not knowledge_configured():
        return _knowledge_unavailable(
            "Knowledge agent is not configured. Set LLM_API_KEY.",
            status_code=503,
        )

    from knowledge.agent import stream_answer_question
    from knowledge.config import get_settings

    settings = get_settings()
    thread_id = body.thread_id or f"ask-{uuid.uuid4()}"

    def event_gen():
        try:
            for event in stream_answer_question(
                question=body.question,
                tenant_id=settings.knowledge_tenant_id,
                access_levels=settings.knowledge_access_levels,
                product=body.product,
                document_type=body.document_type,
                thread_id=thread_id,
            ):
                if event.get("event") == "final" and isinstance(event.get("data"), dict):
                    event = {**event, "thread_id": thread_id, "data": {**event["data"], "thread_id": thread_id}}
                yield f"data: {json.dumps(event, default=str)}\n\n"
        except ValueError as exc:
            yield f"data: {json.dumps({'event': 'error', 'detail': str(exc)})}\n\n"
        except Exception as exc:
            LOGGER.exception("Dashboard ask stream failed")
            yield f"data: {json.dumps({'event': 'error', 'detail': str(exc)})}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/api/dashboard/ask")
def dashboard_ask(request: Request, body: AskBody) -> Response:
    """Session-authenticated ask proxy — tenant/access come from server config only."""
    from knowledge import knowledge_configured, knowledge_deps_available

    if not knowledge_deps_available():
        return _knowledge_unavailable(
            "Knowledge agent extras are not installed. "
            "Run: pip install -e '.[knowledge]'",
            status_code=501,
        )
    if not knowledge_configured():
        return _knowledge_unavailable(
            "Knowledge agent is not configured. Set LLM_API_KEY in the environment.",
            status_code=503,
        )

    try:
        from knowledge.agent import answer_question
        from knowledge.config import get_settings
    except ImportError as exc:
        return _knowledge_unavailable(str(exc), status_code=501)

    settings = get_settings()
    thread_id = body.thread_id or f"ask-{uuid.uuid4()}"
    started = time.perf_counter()

    try:
        result = answer_question(
            question=body.question,
            tenant_id=settings.knowledge_tenant_id,
            access_levels=settings.knowledge_access_levels,
            product=body.product,
            document_type=body.document_type,
            thread_id=thread_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        LOGGER.exception("Dashboard ask failed")
        raise HTTPException(
            status_code=503, detail="QA service temporarily unavailable"
        ) from exc

    elapsed_ms = (time.perf_counter() - started) * 1000
    payload = {
        **result.model_dump(),
        "thread_id": thread_id,
    }
    response = JSONResponse(payload)
    response.headers["X-Response-Time-Ms"] = f"{elapsed_ms:.2f}"
    response.headers["X-Request-ID"] = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    return response
