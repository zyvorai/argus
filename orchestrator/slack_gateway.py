# Copyright 2026 Zyvor AI Labs · https://zyvor.dev
# SPDX-License-Identifier: LicenseRef-Zyvor-Production-1.0
"""Slack slash-command gateway: trigger and check on Mission Control jobs from chat.

Kept deliberately minimal: it replies synchronously, inside Slack's 3-second
window, with the enqueued job id or its current status — reusing the same
`DurableJobService`/`MissionControlStore` queue that `POST /api/v2/jobs`
already uses. It does not follow up on a job's `response_url` once the job
finishes; completion is still reported through the existing
`SLACK_WEBHOOK_URL` notify channel (`agents/reporter/notify.py`). Extending
this to a full round-trip (poll the job and post back to `response_url`) is a
reasonable next step if one-way "did it finish yet" checks prove annoying.
"""

from __future__ import annotations

from typing import Any

SUPPORTED_KINDS = {"smoke", "full", "regression", "audit"}


def _usage() -> dict[str, str]:
    return {
        "response_type": "ephemeral",
        "text": (
            "Usage: `/zyvor run <kind>` (" + ", ".join(sorted(SUPPORTED_KINDS)) + ") "
            "or `/zyvor status <job_id>`"
        ),
    }


def _run(kind: str, *, requested_by: str) -> dict[str, str]:
    if kind not in SUPPORTED_KINDS:
        return {
            "response_type": "ephemeral",
            "text": f"Unknown kind `{kind}`. Supported: {', '.join(sorted(SUPPORTED_KINDS))}",
        }

    from orchestrator.dashboard.durable_jobs import get_service

    try:
        job = get_service().enqueue(kind, {}, requested_by=requested_by)
    except ValueError:
        # Don't echo exception text to Slack — validation detail stays server-side.
        return {
            "response_type": "ephemeral",
            "text": "Could not start job — check kind and parameters.",
        }

    return {
        "response_type": "in_channel",
        "text": (
            f":rocket: Started `{kind}` (job `{job['id']}`) — "
            f"check with `/zyvor status {job['id']}`."
        ),
    }


def _status(job_id: str) -> dict[str, str]:
    from orchestrator.persistence.store import get_store

    job = get_store().get_job(job_id)
    if not job:
        return {"response_type": "ephemeral", "text": f"No job found with id `{job_id}`."}
    return {
        "response_type": "ephemeral",
        "text": f"Job `{job_id}` (`{job.get('kind')}`): *{job.get('status')}*",
    }


def handle_slash_command(text: str, *, requested_by: str) -> dict[str, Any]:
    """Handle a `/zyvor <action> <arg>` slash command and return a Slack reply."""
    parts = text.split()
    if len(parts) < 2:
        return _usage()

    action, arg = parts[0].lower(), parts[1]
    if action == "run":
        return _run(arg, requested_by=requested_by)
    if action == "status":
        return _status(arg)
    return _usage()
