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

"""FastAPI GitHub webhook receiver."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request

from orchestrator.graph import get_compiled_graph
from orchestrator.paths import repo_root as _shared_repo_root
from orchestrator.state import PipelineState


def _verify_signature(payload: bytes, signature: str | None, secret: str) -> bool:
    if not signature or not secret:
        return False
    expected = "sha256=" + hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def _changed_files_from_push(payload: dict[str, Any]) -> list[str]:
    changed: set[str] = set()
    for commit in payload.get("commits", []):
        changed.update(commit.get("added", []))
        changed.update(commit.get("modified", []))
        changed.update(commit.get("removed", []))
    return sorted(changed)


def _build_state_from_event(event: str, payload: dict[str, Any]) -> PipelineState:
    pr_number = None
    repo_full_name = payload.get("repository", {}).get("full_name")
    metadata: dict[str, Any] = {"event": event}
    expand_coverage = os.environ.get("ENABLE_COVERAGE_EXPANSION", "false").lower() == "true"

    if event == "pull_request":
        pr_number = payload.get("pull_request", {}).get("number")
    elif event == "repository_dispatch":
        client_payload = payload.get("client_payload", {})
        pr_number = client_payload.get("pr_number")
    elif event == "push":
        metadata["changed_files"] = _changed_files_from_push(payload)

    return {
        "source": "github",
        "spec_paths": [],
        "spec_contents": [],
        "requirements": [],
        "generated_tests": [],
        "test_results": None,
        "failure_analysis": None,
        "report_path": None,
        "pdf_report_path": None,
        "report_summary": None,
        "pr_number": pr_number,
        "repo_full_name": repo_full_name or os.environ.get("ZYVOR_PRODUCT_REPO"),
        "error": None,
        "metadata": metadata,
        "expand_coverage": expand_coverage,
        "coverage_inventory": [],
        "coverage_gaps": [],
    }


def create_app() -> FastAPI:
    app = FastAPI(title="Zyvor Argus Webhook")

    from urllib.parse import quote

    from fastapi.responses import JSONResponse, RedirectResponse
    from fastapi.staticfiles import StaticFiles

    from orchestrator.dashboard import auth
    from orchestrator.dashboard.knowledge_routes import router as knowledge_dashboard_router
    from orchestrator.dashboard.routes import router as dashboard_router

    app.include_router(dashboard_router)
    app.include_router(knowledge_dashboard_router)

    try:
        from knowledge import knowledge_deps_available
        from knowledge.api import create_knowledge_router

        if knowledge_deps_available():
            app.include_router(create_knowledge_router())
    except Exception:
        # Optional [knowledge] extras — Mission Control still serves without RAG.
        pass

    from orchestrator.enterprise import install_enterprise
    install_enterprise(app)

    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        path = request.url.path
        if auth.requires_auth(path) and not auth.is_authenticated(request):
            if path.startswith(("/api/", "/reports", "/screenshots")):
                return JSONResponse({"detail": "authentication required"}, status_code=401)
            return RedirectResponse(f"/login?next={quote(path)}", status_code=302)

        # CSRF: only relevant for requests actually relying on the
        # auto-attached session cookie for identity. A request carrying its
        # own Authorization bearer token (the /api/v2 service-token path)
        # isn't auto-replayable cross-site the way a cookie is, so it's
        # exempt. Covers /api/dashboard/* (checked above) and /api/v2/*
        # (which auth_middleware otherwise never authenticates — that's
        # rbac.require_scope's job — but a session cookie can drive it too).
        # /api/login is exempt so an already-authenticated browser can
        # re-authenticate (login page has no session CSRF yet / may not
        # attach X-CSRF-Token); credential check is the gate there.
        mutating = request.method not in {"GET", "HEAD", "OPTIONS"}
        if (
            auth.enabled()
            and mutating
            and path.startswith("/api/")
            and path.rstrip("/") != "/api/login"
            and "authorization" not in request.headers
            and auth.is_authenticated(request)
            and not auth.csrf_valid(request)
        ):
            return JSONResponse({"detail": "missing or invalid CSRF token"}, status_code=403)

        return await call_next(request)

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        # Registered after auth_middleware so it wraps outside it and runs
        # first — throttling happens before an (possibly failing) auth check.
        path = request.url.path
        if path.startswith("/api/dashboard") or path.startswith("/api/v2"):
            from orchestrator.security import rate_limit

            forwarded = request.headers.get("x-forwarded-for", "")
            client_ip = (
                forwarded.split(",")[0].strip()
                if forwarded
                else (request.client.host if request.client else "unknown")
            )
            wait = rate_limit.check(client_ip)
            if wait:
                return JSONResponse(
                    {"detail": "rate limit exceeded"},
                    status_code=429,
                    headers={"Retry-After": str(wait)},
                )
        return await call_next(request)

    repo_root = _shared_repo_root()
    for mount, directory in (("/reports", "reports"), ("/screenshots", "screenshots")):
        target = repo_root / directory
        target.mkdir(parents=True, exist_ok=True)
        app.mount(mount, StaticFiles(directory=target), name=directory)
    # Same-origin vendored assets (e.g. mermaid.min.js for the attack-graph
    # report) — the CSP's script-src 'self' blocks a CDN <script src>.
    app.mount("/static/vendor", StaticFiles(directory=repo_root / "templates" / "vendor"), name="vendor")

    @app.get("/health")
    async def health() -> dict[str, Any]:
        payload: dict[str, Any] = {"status": "ok"}
        try:
            from knowledge import knowledge_deps_available
            from knowledge.vectorstore import get_qdrant_client

            if knowledge_deps_available():
                try:
                    get_qdrant_client().get_collections()
                    payload["knowledge"] = "ok"
                    payload["qdrant"] = "reachable"
                except Exception:
                    payload["knowledge"] = "degraded"
                    payload["qdrant"] = "unreachable"
            else:
                payload["knowledge"] = "unavailable"
        except Exception:
            payload["knowledge"] = "unavailable"
        return payload

    @app.post("/webhook/github")
    async def github_webhook(
        request: Request,
        x_github_event: str = Header(None),
        x_hub_signature_256: str = Header(None),
    ) -> dict[str, Any]:
        body = await request.body()
        secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
        event = x_github_event or "unknown"
        delivery_id = request.headers.get("x-github-delivery", "")
        from orchestrator.security.webhook import WebhookSecurityError, verify_github_webhook
        try:
            verification = verify_github_webhook(
                body,
                x_hub_signature_256,
                secret,
                event=event,
                delivery_id=delivery_id,
            )
        except WebhookSecurityError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        if verification.duplicate:
            return {"status": "ignored", "event": event, "reason": "duplicate delivery"}

        payload = json.loads(body)

        supported = {"push", "pull_request", "repository_dispatch"}
        if event not in supported:
            return {"status": "ignored", "event": event}

        if event == "repository_dispatch":
            action = payload.get("action", "")
            if action != "staging-deployed":
                return {"status": "ignored", "action": action}

        try:
            from orchestrator.dashboard import activity

            activity.record_webhook(
                event,
                payload.get("repository", {}).get("full_name"),
                detail=f"PR #{state_pr}" if (state_pr := payload.get("pull_request", {}).get("number")) else "",
            )
        except Exception:
            pass

        state = _build_state_from_event(event, payload)
        graph = get_compiled_graph()
        result = graph.invoke(state)

        test_results = result.get("test_results")
        metadata = result.get("metadata", {})
        return {
            "status": "completed",
            "event": event,
            "passed": test_results.passed if test_results else 0,
            "failed": test_results.failed if test_results else 0,
            "report_path": result.get("report_path"),
            "pdf_report_path": result.get("pdf_report_path"),
            "coverage_inventory_size": metadata.get("coverage_inventory_size"),
            "coverage_gaps_remaining": metadata.get("coverage_gaps_remaining"),
            "coverage_tests_generated": metadata.get("coverage_tests_generated"),
            "error": result.get("error"),
        }

    @app.post("/webhook/slack/command")
    async def slack_command(
        request: Request,
        x_slack_signature: str = Header(None),
        x_slack_request_timestamp: str = Header(None),
    ) -> dict[str, Any]:
        body = await request.body()
        secret = os.environ.get("SLACK_SIGNING_SECRET", "")
        from orchestrator.security.slack import SlackSecurityError, verify_slack_request

        try:
            verify_slack_request(body, x_slack_signature, x_slack_request_timestamp, secret)
        except SlackSecurityError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

        from urllib.parse import parse_qsl

        form = dict(parse_qsl(body.decode("utf-8")))
        text = (form.get("text") or "").strip()
        user = form.get("user_name") or "slack-user"

        from orchestrator.slack_gateway import handle_slash_command

        return handle_slash_command(text, requested_by=f"slack:{user}")

    return app
