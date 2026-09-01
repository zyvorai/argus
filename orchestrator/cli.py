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

"""CLI entry point for Zyvor Argus."""

from __future__ import annotations

import warnings

warnings.filterwarnings("ignore", message=".*OpenSSL.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langgraph.*")

import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv

from orchestrator.graph import get_compiled_graph
from orchestrator.paths import repo_root as _shared_repo_root
from orchestrator.state import PipelineState

app = typer.Typer(
    name="argus",
    help="Zyvor Argus — autonomous testing, security, and monitoring for the Zyvor platform",
    no_args_is_help=True,
)

test_app = typer.Typer(name="test", help="Playwright test generation & execution", no_args_is_help=True)
flow_app = typer.Typer(name="flow", help="Multi-step user journeys", no_args_is_help=True)
vision_app = typer.Typer(name="vision", help="Visual regression & route screenshots", no_args_is_help=True)
api_app = typer.Typer(name="api", help="API/AI/auth contract & workflow testing", no_args_is_help=True)
watch_app = typer.Typer(name="watch", help="Recurring monitoring: vitals & site audits", no_args_is_help=True)
guard_app = typer.Typer(name="guard", help="Security testing & pentesting", no_args_is_help=True)
redteam_app = typer.Typer(name="redteam", help="LLM/application red-teaming", no_args_is_help=True)
ask_app = typer.Typer(name="ask", help="Ask Zyra knowledge base ingestion & evaluation", no_args_is_help=True)

app.add_typer(test_app, name="test")
app.add_typer(flow_app, name="flow")
app.add_typer(vision_app, name="vision")
app.add_typer(api_app, name="api")
app.add_typer(watch_app, name="watch")
app.add_typer(guard_app, name="guard")
app.add_typer(redteam_app, name="redteam")
app.add_typer(ask_app, name="ask")


def _load_env() -> None:
    repo_root = _shared_repo_root()
    load_dotenv(repo_root / ".env")


def _findings_severity_summary(items: list[dict]) -> tuple[dict[str, int], Optional[str]]:
    """Severity counts + the single highest severity, for --fail-on gating
    and reports/summary.json — over *this run's* findings, not the
    (potentially stale) historical findings store."""
    from orchestrator.dashboard.findings import SEVERITY_RANK

    counts: dict[str, int] = {}
    for item in items:
        sev = item.get("severity", "medium")
        counts[sev] = counts.get(sev, 0) + 1
    max_severity = max(counts, key=lambda s: SEVERITY_RANK.get(s, 0)) if counts else None
    return counts, max_severity


def _exceeds_fail_on(max_severity: Optional[str], fail_on: str) -> bool:
    from orchestrator.dashboard.findings import SEVERITY_RANK

    if not max_severity:
        return False
    return SEVERITY_RANK.get(max_severity, 0) >= SEVERITY_RANK.get(fail_on, 3)


def _initial_state(
    source: str = "local",
    spec: Optional[str] = None,
    pr_number: Optional[int] = None,
    expand_coverage: bool = False,
) -> PipelineState:
    spec_paths: list[str] = []
    document_paths: list[str] = []
    if spec:
        if source == "github":
            from github_integration.client import normalize_github_spec_path

            spec_paths = [normalize_github_spec_path(spec)]
        elif source == "document":
            document_paths = [str(Path(spec).resolve())]
        else:
            spec_paths = [str(Path(spec).resolve())]

    env_expand = os.environ.get("ENABLE_COVERAGE_EXPANSION", "false").lower() == "true"

    return {
        "source": source,
        "spec_paths": spec_paths,
        "document_paths": document_paths,
        "spec_contents": [],
        "requirements": [],
        "generated_tests": [],
        "test_results": None,
        "failure_analysis": None,
        "report_path": None,
        "pdf_report_path": None,
        "report_summary": None,
        "pr_number": pr_number,
        "repo_full_name": os.environ.get("ZYVOR_PRODUCT_REPO"),
        "error": None,
        "metadata": {"explicit_spec": bool(spec)},
        "expand_coverage": expand_coverage or env_expand,
        "coverage_inventory": [],
        "coverage_gaps": [],
    }


def _run_discovery_subgraph(state: PipelineState) -> PipelineState:
    from orchestrator.nodes.discover import discover_coverage
    from orchestrator.nodes.fetch import fetch_requirements
    from orchestrator.nodes.gap_analyze import gap_analyze

    state = fetch_requirements(state)
    if state.get("error"):
        return state
    state = discover_coverage(state)
    return gap_analyze(state)


@test_app.command()
def run(
    source: str = typer.Option("local", help="Requirement source: local | github | document"),
    spec: Optional[str] = typer.Option(
        None,
        help="Spec path: local file, GitHub repo path (docs/specs/foo.md), or GitHub blob URL",
    ),
    pr_number: Optional[int] = typer.Option(None, help="PR number for GitHub comment"),
    expand_coverage: bool = typer.Option(
        False,
        "--expand-coverage",
        help="Discover routes/pages from GitHub code/docs and generate missing tests",
    ),
) -> None:
    """Run the full QA pipeline: fetch → parse → evaluate_quality → generate → execute → report → notify."""
    _load_env()
    t0 = time.time()
    started_at = datetime.fromtimestamp(t0, tz=timezone.utc).isoformat()
    graph = get_compiled_graph()
    state = _initial_state(
        source=source,
        spec=spec,
        pr_number=pr_number,
        expand_coverage=expand_coverage,
    )
    result = graph.invoke(state)

    from agents.reporter.summary import write_ci_summary

    base_url = os.environ.get("ZYVOR_BASE_URL")

    if result.get("error"):
        typer.echo(f"Pipeline error: {result['error']}", err=True)
        tr = result.get("test_results")
        if tr:
            typer.echo(
                f"Partial results: {tr.passed} passed, {tr.failed} failed",
                err=True,
            )
        write_ci_summary(
            command="run",
            target_url=base_url,
            passed=tr.passed if tr else 0,
            failed=tr.failed if tr else 0,
            total=tr.total if tr else 0,
            exit_code=1,
            started_at=started_at,
            duration_s=time.time() - t0,
            extra={"pipeline_error": result["error"]},
        )
        raise typer.Exit(code=1)

    test_results = result.get("test_results")
    metadata = result.get("metadata", {})
    if metadata.get("coverage_inventory_size") is not None:
        typer.echo(
            f"Coverage: {metadata.get('coverage_inventory_size', 0)} candidates, "
            f"{metadata.get('coverage_gaps_remaining', 0)} gaps, "
            f"{metadata.get('coverage_tests_generated', 0)} new tests"
        )
    if test_results:
        typer.echo(
            f"Results: {test_results.passed} passed, "
            f"{test_results.failed} failed, {test_results.total} total"
        )
        generated = result.get("generated_tests", [])
        if generated:
            typer.echo(f"Generated tests: {len(generated)} file(s)")
    if result.get("report_path"):
        typer.echo(f"Report: {result['report_path']}")
    if result.get("pdf_report_path"):
        typer.echo(f"PDF report: {result['pdf_report_path']}")

    failed = bool(test_results and test_results.failed > 0)
    write_ci_summary(
        command="run",
        target_url=base_url,
        passed=test_results.passed if test_results else 0,
        failed=test_results.failed if test_results else 0,
        total=test_results.total if test_results else 0,
        exit_code=1 if failed else 0,
        started_at=started_at,
        duration_s=time.time() - t0,
        artifacts={
            "report_html": result.get("report_path"),
            "report_pdf": result.get("pdf_report_path"),
        },
    )
    if failed:
        raise typer.Exit(code=1)


@test_app.command("exec")
def test(
    grep: Optional[str] = typer.Option(None, help="Playwright --grep filter (e.g. @smoke)"),
    shard: Optional[str] = typer.Option(None, help="Playwright --shard i/n (e.g. 1/2)"),
) -> None:
    """Run Playwright tests only (skip parse/generate)."""
    _load_env()
    t0 = time.time()
    started_at = datetime.fromtimestamp(t0, tz=timezone.utc).isoformat()
    from agents.execution.runner import run_playwright
    from agents.reporter.summary import write_ci_summary

    base_url = os.environ.get("ZYVOR_BASE_URL", "https://zyvor.dev")
    repo_root = _shared_repo_root()
    test_dirs = [str(repo_root / "tests" / "manual")]
    grep = grep or os.environ.get("ZYVOR_GREP")
    shard = shard or os.environ.get("ZYVOR_SHARD")

    extra = []
    if grep:
        extra.append(f"grep={grep}")
    if shard:
        extra.append(f"shard={shard}")
    typer.echo(f"Running Playwright tests against {base_url}" + (f" ({', '.join(extra)})" if extra else "") + "...")
    results = run_playwright(
        test_dirs=test_dirs,
        base_url=base_url,
        grep=grep,
        shard=shard,
    )
    typer.echo(f"Results: {results.passed} passed, {results.failed} failed")

    failed = results.failed > 0
    write_ci_summary(
        command="test",
        target_url=base_url,
        passed=results.passed,
        failed=results.failed,
        skipped=results.skipped,
        total=results.total,
        exit_code=1 if failed else 0,
        started_at=started_at,
        duration_s=time.time() - t0,
        artifacts={"raw_json": "reports/results.json"},
    )
    if failed:
        raise typer.Exit(code=1)


@test_app.command()
def generate(
    spec: Optional[str] = typer.Option(
        None,
        help="Spec path: local file, GitHub repo path (docs/specs/foo.md), or GitHub blob URL",
    ),
    source: str = typer.Option("local", help="Requirement source: local | github | document"),
    expand_coverage: bool = typer.Option(
        False,
        "--expand-coverage",
        help="Discover routes/pages from GitHub code/docs and generate missing tests",
    ),
) -> None:
    """Parse spec and generate Playwright tests (no execution)."""
    _load_env()

    subgraph_nodes = ["fetch", "discover", "gap_analyze", "parse", "evaluate_quality", "generate"]
    state = _initial_state(source=source, spec=spec, expand_coverage=expand_coverage)

    for node in subgraph_nodes:
        if node == "fetch":
            from orchestrator.nodes.fetch import fetch_requirements

            state = fetch_requirements(state)
        elif node == "discover":
            from orchestrator.nodes.discover import discover_coverage

            state = discover_coverage(state)
        elif node == "gap_analyze":
            from orchestrator.nodes.gap_analyze import gap_analyze

            state = gap_analyze(state)
        elif node == "parse":
            from orchestrator.nodes.parse import parse_requirements

            state = parse_requirements(state)
        elif node == "evaluate_quality":
            from orchestrator.nodes.evaluate_quality import evaluate_quality

            state = evaluate_quality(state)
        elif node == "generate":
            from orchestrator.nodes.generate import generate_tests

            state = generate_tests(state)

    if state.get("error"):
        typer.echo(f"Error: {state['error']}", err=True)
        raise typer.Exit(code=1)

    metadata = state.get("metadata", {})
    if metadata.get("coverage_inventory_size") is not None:
        typer.echo(
            f"Coverage: {metadata.get('coverage_inventory_size', 0)} candidates, "
            f"{metadata.get('coverage_gaps_remaining', 0)} gaps, "
            f"{metadata.get('coverage_tests_generated', 0)} new tests"
        )

    generated = state.get("generated_tests", [])
    typer.echo(f"Generated {len(generated)} test file(s):")
    for path in generated:
        typer.echo(f"  {path}")


@test_app.command()
def discover(
    source: str = typer.Option("github", help="Requirement source: local | github | document"),
    spec: Optional[str] = typer.Option(
        None,
        help="Optional spec path when fetching from GitHub",
    ),
    pr_number: Optional[int] = typer.Option(None, help="PR number for changed-file scoping"),
) -> None:
    """Discover coverage inventory and gaps without generating or running tests."""
    _load_env()
    state = _initial_state(
        source=source,
        spec=spec,
        pr_number=pr_number,
        expand_coverage=True,
    )
    state = _run_discovery_subgraph(state)

    if state.get("error"):
        typer.echo(f"Error: {state['error']}", err=True)
        raise typer.Exit(code=1)

    inventory = state.get("coverage_inventory", [])
    gaps = state.get("coverage_gaps", [])
    metadata = state.get("metadata", {})

    typer.echo(f"Discovered {len(inventory)} coverage candidate(s)")
    typer.echo(f"Uncovered gaps: {len(gaps)}")
    if metadata.get("discovered_paths"):
        typer.echo(f"Files scanned: {len(metadata['discovered_paths'])}")

    for gap in gaps[:20]:
        candidate = gap.candidate
        typer.echo(f"  [gap] {candidate.kind} {candidate.path} — {candidate.title}")
    if len(gaps) > 20:
        typer.echo(f"  ... and {len(gaps) - 20} more")


@test_app.command()
def create(
    description: str = typer.Argument(..., help="Natural language test description"),
    execute: bool = typer.Option(False, help="Run generated tests immediately"),
) -> None:
    """Create Playwright tests from natural language (Phase 4)."""
    _load_env()
    from agents.nl_create.agent import create_and_generate, create_from_natural_language
    from agents.parser.agent import save_requirements

    repo_root = _shared_repo_root()
    output_dir = repo_root / "tests" / "generated"

    typer.echo(f"Creating test from: {description}")
    try:
        parsed = create_from_natural_language(description)
    except Exception as exc:
        typer.echo(f"NL parsing failed: {exc}", err=True)
        raise typer.Exit(code=1)

    save_requirements(parsed, repo_root / "tests" / "fixtures" / "requirements.json")

    try:
        generated = create_and_generate(description, str(output_dir))
    except Exception as exc:
        typer.echo(f"Test generation failed: {exc}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Generated {len(generated)} test file(s):")
    for path in generated:
        typer.echo(f"  {path}")

    if execute:
        from agents.execution.runner import run_playwright

        results = run_playwright(test_dirs=[str(output_dir)])
        typer.echo(f"Results: {results.passed} passed, {results.failed} failed")
        if results.failed > 0:
            raise typer.Exit(code=1)


@vision_app.command()
def regression(
    update_baselines: bool = typer.Option(False, help="Update screenshot baselines"),
) -> None:
    """Run visual regression check (Phase 2)."""
    _load_env()
    if update_baselines:
        os.environ["UPDATE_BASELINES"] = "true"
    os.environ["ENABLE_REGRESSION"] = "true"

    from orchestrator.nodes.regression import regression_check

    from agents.execution.runner import run_playwright

    base_url = os.environ.get("ZYVOR_BASE_URL", "https://zyvor.dev")
    repo_root = _shared_repo_root()
    test_dirs = [str(repo_root / "tests" / "manual")]

    typer.echo("Running tests with screenshot capture...")
    test_results = run_playwright(test_dirs=test_dirs, base_url=base_url)

    state = regression_check({"test_results": test_results})
    diffs = state.get("regression_diffs", [])

    for d in diffs:
        status = "✓" if d.status == "pass" else "✗"
        typer.echo(f"  {status} {d.file}: {d.diff_percent}% — {d.message or d.status}")

    failed = [d for d in diffs if d.status == "fail"]
    if failed:
        raise typer.Exit(code=1)


@flow_app.command("run")
def flow(
    url: str = typer.Argument(..., help="Base URL to run the journey against"),
    describe: Optional[str] = typer.Option(None, help="Journey in plain English"),
    steps: Optional[str] = typer.Option(None, help="Path to a file with one step per line"),
    video: bool = typer.Option(True, help="Record the journey as a video"),
    trace: bool = typer.Option(True, help="Capture a Playwright trace.zip (time-travel debugger)"),
    insecure: bool = typer.Option(False, help="Accept self-signed TLS"),
    username: Optional[str] = typer.Option(None, help="Login username (best-effort sign-in)"),
    password: Optional[str] = typer.Option(None, help="Login password"),
    session: Optional[str] = typer.Option(None, help="Reuse a saved session file (path or name under reports/artifacts/auth)"),
    browser: Optional[str] = typer.Option(None, help="Browser engine: chromium | firefox | webkit"),
    device: Optional[str] = typer.Option(None, help="Playwright device profile, e.g. 'iPhone 14'"),
    throttle: Optional[str] = typer.Option(None, help="Network throttle: 3g | offline"),
) -> None:
    """Drive a multi-step user journey and record it end-to-end as one video."""
    _load_env()
    t0 = time.time()
    started_at = datetime.fromtimestamp(t0, tz=timezone.utc).isoformat()
    import os as _os

    from agents.flow.engine import run_flow
    from agents.flow.parse import parse_flow
    from agents.reporter.summary import write_ci_summary

    if browser in ("chromium", "firefox", "webkit"):
        _os.environ["ZYVOR_BROWSER"] = browser
    if device:
        _os.environ["ZYVOR_DEVICE"] = device
    if throttle in ("3g", "offline"):
        _os.environ["ZYVOR_THROTTLE"] = throttle

    if steps:
        text, steps_mode = Path(steps).read_text(encoding="utf-8"), True
    elif describe:
        text, steps_mode = describe, False
    else:
        typer.echo("Provide --describe or --steps", err=True)
        raise typer.Exit(code=2)

    parsed, mode = parse_flow(text, steps_mode=steps_mode)
    typer.echo(f"{len(parsed)} step(s) parsed ({mode})")
    repo_root = _shared_repo_root()
    out_dir = repo_root / "reports" / "artifacts" / "flows" / "cli"
    session_path = ""
    if session:
        cand = Path(session)
        if not cand.exists():
            cand = repo_root / "reports" / "artifacts" / "auth" / session
        session_path = str(cand) if cand.exists() else ""
        if session_path:
            typer.echo(f"reusing session {session_path}")
    result = run_flow(
        url, parsed, out_dir, record=video, trace=trace, insecure=insecure,
        username=username or "", password=password or "", session=session_path,
        on_line=lambda line: typer.echo(line),
    )
    typer.echo(f"Result: {result['passed']}/{result['total']} steps passed")
    if result.get("video"):
        typer.echo(f"Journey video: {out_dir / result['video']}")
    if result.get("trace"):
        typer.echo(f"Trace (open at trace.playwright.dev): {out_dir / result['trace']}")
    failed = result["failed"] > 0
    write_ci_summary(
        command="flow",
        target_url=url,
        passed=result["passed"],
        failed=result["failed"],
        total=result["total"],
        exit_code=1 if failed else 0,
        started_at=started_at,
        duration_s=time.time() - t0,
        artifacts={
            "video": str(out_dir / result["video"]) if result.get("video") else None,
            "trace": str(out_dir / result["trace"]) if result.get("trace") else None,
        },
    )
    if failed:
        raise typer.Exit(code=1)


@vision_app.command(name="route-sweep")
def route_sweep(
    url: str = typer.Argument(..., help="Base URL"),
    routes: str = typer.Option("/", help="Comma-separated routes to screenshot"),
    mobile: bool = typer.Option(False, help="Also capture mobile viewport"),
    update_baselines: bool = typer.Option(False, help="Capture/replace baselines"),
    auto: bool = typer.Option(False, help="Auto-discover routes by crawling the site"),
    max_pages: int = typer.Option(20, help="Max routes to discover when --auto"),
    insecure: bool = typer.Option(False, help="Accept self-signed TLS"),
) -> None:
    """Screenshot a list of routes and diff against baselines."""
    _load_env()
    t0 = time.time()
    started_at = datetime.fromtimestamp(t0, tz=timezone.utc).isoformat()
    from orchestrator.dashboard.jobs import _job_route_sweep
    from agents.reporter.summary import write_ci_summary

    vps = ["desktop"] + (["mobile"] if mobile else [])
    result = _job_route_sweep({
        "url": url,
        "routes": [r.strip() for r in routes.split(",") if r.strip()],
        "viewports": vps,
        "update_baselines": update_baselines,
        "insecure": insecure,
        "auto": auto,
        "max_pages": max_pages,
    })
    typer.echo(f"Swept {result['routes']} route(s): {result['fail_count']} changed, {result['new_baselines']} new baseline(s)")
    for row in result["sweep_rows"]:
        typer.echo(f"  {row['status']:8} {row['route']} [{row['viewport']}] {row['diff']}%")

    fail_count = result["fail_count"]
    total_rows = len(result["sweep_rows"])
    write_ci_summary(
        command="route-sweep",
        target_url=url,
        passed=total_rows - fail_count,
        failed=fail_count,
        total=total_rows,
        exit_code=1 if fail_count > 0 else 0,
        started_at=started_at,
        duration_s=time.time() - t0,
        artifacts={"report_html": (result.get("report") or {}).get("html")},
        extra={"new_baselines": result["new_baselines"], "routes": result["routes"]},
    )
    if fail_count > 0:
        raise typer.Exit(code=1)


@api_app.command(name="test")
def api_test(
    base: str = typer.Argument(..., help="API base URL"),
    spec: Optional[str] = typer.Option(None, help="OpenAPI spec URL or local JSON file"),
    workflow: Optional[str] = typer.Option(None, help="JSON file with an ordered workflow of steps"),
    include_writes: bool = typer.Option(False, help="Also exercise POST/PUT/PATCH/DELETE endpoints"),
    token: Optional[str] = typer.Option(None, help="Bearer token for auth"),
    api_key: Optional[str] = typer.Option(None, help="API key (sent as x-api-key)"),
    insecure: bool = typer.Option(False, help="Accept self-signed TLS"),
) -> None:
    """Validate REST endpoints against their OpenAPI schema, or run an API workflow."""
    _load_env()
    import json as _json

    from orchestrator.dashboard.jobs import _job_api_contract

    spec_val = None
    if spec:
        if spec.startswith(("http://", "https://")):
            spec_val = spec
        else:
            spec_val = _json.loads(Path(spec).read_text(encoding="utf-8"))
    wf = _json.loads(Path(workflow).read_text(encoding="utf-8")) if workflow else None
    auth = {}
    if token:
        auth["token"] = token
    if api_key:
        auth["apiKey"] = api_key

    result = _job_api_contract({
        "url": base,
        "mode": "workflow" if wf else "spec",
        "spec": spec_val,
        "workflow": wf,
        "auth": auth or None,
        "include_writes": include_writes,
        "insecure": insecure,
        "max_endpoints": 200,
        "path_params": None,
    })
    typer.echo(f"API contract ({result['mode']}): {result['passed']}/{result['total']} passed")
    rows = result.get("endpoints") if result["mode"] == "spec" else result.get("steps")
    for r in rows or []:
        mark = "✓" if r.get("ok") else "✗"
        label = f"{r.get('method')} {r.get('path')}" if result["mode"] == "spec" else r.get("desc")
        detail = " | ".join(r.get("schema_errors") or []) or r.get("error") or r.get("note") or ""
        typer.echo(f"  {mark} {label} → {r.get('status')} {detail}")
    if result["failed"] > 0:
        raise typer.Exit(code=1)


@api_app.command(name="ai-test")
def ai_test(
    url: str = typer.Argument(..., help="App URL to drive"),
    goal: str = typer.Option(..., "--goal", "-g", help="Plain-English goal, e.g. 'create a ubuntu vm 1 vcpu 2gb ram'"),
    session: Optional[str] = typer.Option(None, help="Reuse a saved session (name under reports/artifacts/auth)"),
    max_steps: int = typer.Option(20, help="Max agent steps"),
    insecure: bool = typer.Option(False, help="Accept self-signed TLS"),
) -> None:
    """Autonomous AI tester — describe a goal and the agent drives the browser to do it."""
    _load_env()
    from orchestrator.dashboard.jobs import _job_ai_flow

    result = _job_ai_flow({"url": url, "goal": goal, "session": session or "",
                           "max_steps": max_steps, "insecure": insecure})
    typer.echo(f"\nAI agent ({result.get('mode')}): {'✅ ' + result['summary'] if result['success'] else '⚠ ' + result['summary']}")
    for s in result.get("ai_steps", []):
        mark = "✓" if s["status"] == "passed" else "✗"
        typer.echo(f"  {mark} step {s['n']}: {s['desc']}")
    if not result["success"]:
        raise typer.Exit(code=1)


@api_app.command(name="auth-test")
def auth_test(
    base: str = typer.Argument(..., help="App base URL"),
    login_url: Optional[str] = typer.Option(None, help="Login page path to drive in-browser"),
    api_login: Optional[str] = typer.Option(None, help="API login endpoint to POST credentials to"),
    protected: str = typer.Option("/", help="A protected path that requires auth"),
    logout_url: Optional[str] = typer.Option(None, help="Logout endpoint (to test session clearing)"),
    username: Optional[str] = typer.Option(None, help="Login username"),
    password: Optional[str] = typer.Option(None, help="Login password"),
    save_session: bool = typer.Option(True, help="Save the session for reuse by flow/realtime"),
    insecure: bool = typer.Option(False, help="Accept self-signed TLS"),
) -> None:
    """Log in, capture a reusable session, and assert auth/session behaviour."""
    _load_env()
    from orchestrator.dashboard.jobs import _job_auth_test

    result = _job_auth_test({
        "url": base, "login_url": login_url or "", "api_login": api_login or "",
        "protected": protected, "logout_url": logout_url or "",
        "username": username or "", "password": password or "",
        "save_session": save_session, "insecure": insecure,
    })
    typer.echo(f"Auth & session: {result['passed']}/{result['total']} checks passed")
    for c in result.get("checks") or []:
        typer.echo(f"  {'✓' if c['ok'] else '✗'} {c['name']} — {c.get('detail', '')}")
    if result.get("session_name"):
        typer.echo(f"Session saved as: {result['session_name']} (reuse with flow/realtime --session)")
    if result["failed"] > 0:
        raise typer.Exit(code=1)


@api_app.command(name="har-replay")
def har_replay(
    url: str = typer.Argument(..., help="Base URL"),
    mode: str = typer.Option("replay", help="record | replay"),
    har: Optional[str] = typer.Option(None, help="HAR file path (required for replay; default out dir for record)"),
    routes: Optional[str] = typer.Option("/", help="Comma/newline list of paths to visit when recording"),
    expect_text: Optional[str] = typer.Option(None, help="Text that must appear during replay"),
    not_found_ok: bool = typer.Option(False, help="On replay, fall back to network if a route is missing from HAR"),
    insecure: bool = typer.Option(False, help="Accept self-signed TLS"),
) -> None:
    """Record network traffic as HAR, or replay a page against a HAR file."""
    _load_env()
    from orchestrator.dashboard.jobs import _job_har_replay

    result = _job_har_replay({
        "url": url,
        "mode": mode,
        "har": har or os.environ.get("ZYVOR_HAR_PATH") or "",
        "routes": routes or "/",
        "expect_text": expect_text or "",
        "not_found_ok": not_found_ok,
        "insecure": insecure,
    })
    typer.echo(f"HAR {result.get('mode')}: {result['passed']}/{result['total']} checks")
    if result.get("har"):
        typer.echo(f"HAR file: {result['har']}")
    for c in result.get("checks") or []:
        typer.echo(f"  {'✓' if c['ok'] else '✗'} {c['name']} — {c.get('detail', '')}")
    if result["failed"] > 0:
        raise typer.Exit(code=1)


@test_app.command(name="import-codegen")
def import_codegen_cmd(
    source: str = typer.Argument(..., help="Path to a Playwright codegen .js/.ts file, or '-' for stdin"),
    url: Optional[str] = typer.Option(None, help="Base URL (required with --run)"),
    run: bool = typer.Option(False, help="Run the imported steps as a flow test"),
    insecure: bool = typer.Option(False, help="Accept self-signed TLS"),
) -> None:
    """Parse Playwright codegen output into flow steps (optionally run them)."""
    _load_env()
    if source == "-":
        script = sys.stdin.read()
    else:
        script = Path(source).read_text(encoding="utf-8")
    from orchestrator.dashboard.jobs import _job_import_codegen

    result = _job_import_codegen({
        "script": script,
        "url": url or "",
        "run": run,
        "insecure": insecure,
    })
    steps = result.get("imported_steps") or result.get("steps") or []
    typer.echo(f"Imported {len(steps)} step(s)")
    for i, s in enumerate(steps, 1):
        typer.echo(f"  {i}. {s.get('action')} {s.get('target') or s.get('assertion') or s.get('value') or ''}")
    if run and result.get("failed", 0) > 0:
        raise typer.Exit(code=1)


@flow_app.command()
def realtime(
    url: str = typer.Argument(..., help="App base URL"),
    ws: Optional[str] = typer.Option(None, help="WebSocket path or full ws(s):// URL"),
    sse: Optional[str] = typer.Option(None, help="SSE endpoint path"),
    ticket_url: Optional[str] = typer.Option(None, help="One-time WS-ticket issue endpoint"),
    token: Optional[str] = typer.Option(None, help="Auth token (Bearer/subprotocol/query)"),
    subprotocol_jwt: bool = typer.Option(False, help="Send token via Sec-WebSocket-Protocol: <name>,<jwt>"),
    ws_subprotocol: str = typer.Option("access_token", help="WS subprotocol name (packetwolf: access_token, zeus-os: zeus-os-auth)"),
    token_query: str = typer.Option("token", help="Query-param name for the token (zeus-os: zeus_os_token)"),
    expect_messages: int = typer.Option(1, help="Minimum messages expected in the window"),
    window_ms: int = typer.Option(15000, help="Observation window (ms)"),
    live_selector: Optional[str] = typer.Option(None, help="CSS selector of a live region to watch for updates"),
    session: Optional[str] = typer.Option(None, help="Reuse a saved session (name under reports/artifacts/auth)"),
    insecure: bool = typer.Option(False, help="Accept self-signed TLS"),
) -> None:
    """Assert WebSocket/SSE streams are live and dashboard live regions update."""
    _load_env()
    from orchestrator.dashboard.jobs import _job_realtime

    result = _job_realtime({
        "url": url, "ws": ws or "", "sse": sse or "", "ticket_url": ticket_url or "",
        "ticket_query": "ticket", "token": token or "", "token_query": token_query,
        "ws_subprotocol": ws_subprotocol, "subprotocol_jwt": subprotocol_jwt,
        "expect_messages": expect_messages, "window_ms": window_ms,
        "live_selector": live_selector or "", "session": session or "", "insecure": insecure,
    })
    typer.echo(f"Live data: {result['passed']}/{result['total']} checks passed")
    for c in result.get("checks") or []:
        typer.echo(f"  {'✓' if c['ok'] else '✗'} {c['name']} — {c.get('detail', '')}")
    if result["failed"] > 0:
        raise typer.Exit(code=1)


@watch_app.command()
def vitals(
    url: str = typer.Argument(..., help="URL to measure"),
    device: Optional[str] = typer.Option(None, help="Playwright device profile, e.g. 'iPhone 14'"),
    throttle: Optional[str] = typer.Option(None, help="Network throttle: 3g | offline"),
    insecure: bool = typer.Option(False, help="Accept self-signed TLS"),
) -> None:
    """Measure Core Web Vitals (LCP/CLS/INP/FCP/TTFB) and grade them."""
    _load_env()
    t0 = time.time()
    started_at = datetime.fromtimestamp(t0, tz=timezone.utc).isoformat()
    from orchestrator.dashboard.jobs import _job_vitals
    from agents.reporter.summary import write_ci_summary

    result = _job_vitals({"url": url, "device": device or "", "throttle": throttle or "", "insecure": insecure})
    typer.echo(f"Overall: {result.get('overall', '?').upper()}")
    metrics = result.get("metrics") or {}
    for name, m in metrics.items():
        typer.echo(f"  {name:5} {str(m.get('value')):>8}  [{m.get('grade')}]")

    total = len(metrics)
    passed = sum(1 for m in metrics.values() if m.get("grade") == "good")
    failed = total - passed
    write_ci_summary(
        command="vitals",
        target_url=url,
        passed=passed,
        failed=failed,
        total=total,
        exit_code=1 if failed > 0 else 0,
        started_at=started_at,
        duration_s=time.time() - t0,
        artifacts={"report_html": (result.get("report") or {}).get("html")},
        extra={"overall": result.get("overall"), "metrics": metrics},
    )
    if failed > 0:
        raise typer.Exit(code=1)


@watch_app.command()
def audit(
    url: str = typer.Argument(..., help="Site to audit"),
    max_pages: int = typer.Option(10, help="Max pages to crawl"),
    checks: Optional[str] = typer.Option(None, help="Comma-separated checks (default: a11y,seo,console,links,perf,headers)"),
    insecure: bool = typer.Option(False, help="Accept self-signed TLS"),
    fail_on: str = typer.Option("high", "--fail-on", help="Exit 1 if any finding is at/above this severity"),
) -> None:
    """Crawl a site and run per-page QA checks (a11y/SEO/perf/security), A-F graded."""
    _load_env()
    t0 = time.time()
    started_at = datetime.fromtimestamp(t0, tz=timezone.utc).isoformat()
    from agents.reporter.summary import write_ci_summary
    from orchestrator.dashboard.jobs import _job_audit

    result = _job_audit({
        "url": url, "max_pages": max_pages,
        "checks": [c.strip() for c in (checks or "").split(",") if c.strip()] or None,
        "insecure": insecure,
    })
    typer.echo(f"Grade: {result['grade']} ({result['score']}/100) — {result['fail_count']} failing, {result['warn_count']} warning checks")
    counts, max_severity = _findings_severity_summary(result.get("findings") or [])
    gate = _exceeds_fail_on(max_severity, fail_on)
    write_ci_summary(
        command="audit", target_url=url,
        passed=result["pages_audited"] - result["fail_count"], failed=result["fail_count"], total=result["pages_audited"],
        exit_code=1 if gate else 0, started_at=started_at, duration_s=time.time() - t0,
        artifacts={"report_html": (result.get("report") or {}).get("html")},
        findings_by_severity=counts, max_severity=max_severity,
        extra={"grade": result["grade"], "score": result["score"]},
    )
    if gate:
        raise typer.Exit(code=1)


@guard_app.command(name="misconfig-scan")
def misconfig_scan(
    url: str = typer.Argument(..., help="Site to scan"),
    engagement_id: str = typer.Option(..., "--engagement-id", help="Authorized security engagement id (POST /api/v2/engagements)"),
    max_paths: int = typer.Option(60, help="Max wordlist paths to probe (capped at 300)"),
    insecure: bool = typer.Option(False, help="Accept self-signed TLS"),
    fail_on: str = typer.Option("high", "--fail-on", help="Exit 1 if any finding is at/above this severity"),
) -> None:
    """Deeper misconfig/recon: tech fingerprinting, path discovery, header grading, DNS hygiene."""
    _load_env()
    t0 = time.time()
    started_at = datetime.fromtimestamp(t0, tz=timezone.utc).isoformat()
    from agents.reporter.summary import write_ci_summary
    from orchestrator.dashboard.jobs import _job_misconfig_scan, _validate

    params = _validate("misconfig_scan", {
        "url": url, "max_paths": max_paths, "insecure": insecure, "engagement_id": engagement_id,
    })
    result = _job_misconfig_scan(params)
    exposed = len(result["paths"]["exposed"])
    typer.echo(f"Grade: {result['grade']} ({result['score']}/100) — {exposed} exposed path(s), headers {result['headers']['status']}")
    counts, max_severity = _findings_severity_summary(result.get("findings") or [])
    gate = _exceeds_fail_on(max_severity, fail_on)
    write_ci_summary(
        command="misconfig-scan", target_url=url,
        passed=0 if exposed else 1, failed=1 if exposed else 0, total=1,
        exit_code=1 if gate else 0, started_at=started_at, duration_s=time.time() - t0,
        findings_by_severity=counts, max_severity=max_severity,
        extra={"grade": result["grade"], "score": result["score"]},
    )
    if gate:
        raise typer.Exit(code=1)


@guard_app.command(name="cve-lookup")
def cve_lookup(
    url: str = typer.Argument(..., help="Site to fingerprint"),
    engagement_id: str = typer.Option(..., "--engagement-id", help="Authorized security engagement id (POST /api/v2/engagements)"),
    insecure: bool = typer.Option(False, help="Accept self-signed TLS"),
    fail_on: str = typer.Option("high", "--fail-on", help="Exit 1 if any finding is at/above this severity"),
) -> None:
    """Read-only CVE lookup: fingerprint tech/versions, check against OSV.dev. No PoC generated or run."""
    _load_env()
    t0 = time.time()
    started_at = datetime.fromtimestamp(t0, tz=timezone.utc).isoformat()
    from agents.reporter.summary import write_ci_summary
    from orchestrator.dashboard.jobs import _job_cve_lookup, _validate

    params = _validate("cve_lookup", {"url": url, "insecure": insecure, "engagement_id": engagement_id})
    result = _job_cve_lookup(params)
    typer.echo(f"{result['total_matches']} known advisory match(es) across {len(result['identified'])} identified component(s)")
    for item in result["identified"]:
        typer.echo(f"  {item['product']} {item['version']} (via {item['source']})")
    counts, max_severity = _findings_severity_summary(result.get("findings") or [])
    gate = _exceeds_fail_on(max_severity, fail_on)
    write_ci_summary(
        command="cve-lookup", target_url=url,
        passed=0 if result["total_matches"] else 1, failed=1 if result["total_matches"] else 0, total=1,
        exit_code=1 if gate else 0, started_at=started_at, duration_s=time.time() - t0,
        findings_by_severity=counts, max_severity=max_severity,
        extra={"total_matches": result["total_matches"]},
    )
    if gate:
        raise typer.Exit(code=1)


@redteam_app.command(name="llm")
def llm_redteam(
    engagement_id: str = typer.Option(..., "--engagement-id", help="Authorized security engagement id (POST /api/v2/engagements)"),
    target: str = typer.Option("dashboard_ask", help="dashboard_ask (in-process) or v1_qa (external)"),
    base_url: Optional[str] = typer.Option(None, "--base-url", help="Required for target=v1_qa"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="Required for target=v1_qa"),
    categories: Optional[str] = typer.Option(None, help="Comma-separated categories (default: all)"),
    max_prompts: int = typer.Option(40, help="Max battery prompts to run (capped at 40)"),
    fail_on: str = typer.Option("high", "--fail-on", help="Exit 1 if any finding is at/above this severity"),
) -> None:
    """Attacker/judge red-team loop against Ask Zyra — jailbreak, prompt-injection, system-prompt-leak resistance."""
    _load_env()
    t0 = time.time()
    started_at = datetime.fromtimestamp(t0, tz=timezone.utc).isoformat()
    from agents.reporter.summary import write_ci_summary
    from orchestrator.dashboard.jobs import _job_llm_redteam, _validate

    params = _validate("llm_redteam", {
        "target": target, "base_url": base_url or "", "api_key": api_key or "",
        "categories": [c.strip() for c in (categories or "").split(",") if c.strip()] or None,
        "max_prompts": max_prompts, "engagement_id": engagement_id,
    })
    result = _job_llm_redteam(params)
    typer.echo(f"Grade: {result['grade']} ({result['score']}/100) — {result['resisted']}/{result['total']} prompts resisted")
    counts, max_severity = _findings_severity_summary(result.get("findings") or [])
    gate = _exceeds_fail_on(max_severity, fail_on)
    write_ci_summary(
        command="llm-redteam", target_url=target,
        passed=result["resisted"], failed=result["total"] - result["resisted"], total=result["total"],
        exit_code=1 if gate else 0, started_at=started_at, duration_s=time.time() - t0,
        findings_by_severity=counts, max_severity=max_severity,
        extra={"grade": result["grade"], "score": result["score"]},
    )
    if gate:
        raise typer.Exit(code=1)


@guard_app.command(name="exploit-poc")
def exploit_poc(
    url: str = typer.Argument(..., help="Target URL"),
    finding_description: str = typer.Option(..., "--finding", help="Describe what to verify"),
    engagement_id: str = typer.Option(..., "--engagement-id", help="Must be an 'exploit'-tier engagement"),
    timeout_s: int = typer.Option(60, "--timeout", help="Sandbox execution timeout in seconds (capped at 300)"),
    fail_on: str = typer.Option("high", "--fail-on", help="Exit 1 if any finding is at/above this severity"),
) -> None:
    """Generate a non-destructive verification PoC via LLM and run it sandboxed in Kubernetes.

    Requires ZYVOR_EXPLOIT_EXECUTION_ENABLED=true and a live sandbox backend
    (kubernetes/sandbox.yaml, ZYVOR_SANDBOX_NAMESPACE) in addition to the
    exploit-tier engagement — see docs/enterprise-v2.md.
    """
    _load_env()
    t0 = time.time()
    started_at = datetime.fromtimestamp(t0, tz=timezone.utc).isoformat()
    from agents.reporter.summary import write_ci_summary
    from orchestrator.dashboard.jobs import _job_exploit_poc, _validate

    params = _validate("exploit_poc", {
        "url": url, "finding_description": finding_description,
        "timeout_s": timeout_s, "engagement_id": engagement_id,
    })
    result = _job_exploit_poc(params)
    typer.echo(f"{'VERIFIED' if result['verified'] else 'not verified'}" + (f" — {result['reason']}" if result['reason'] else ""))
    typer.echo(f"PoC: {result['poc_path']} (sha256 {result['code_sha256'][:12]}…)")
    counts, max_severity = _findings_severity_summary(result.get("findings") or [])
    gate = _exceeds_fail_on(max_severity, fail_on)
    write_ci_summary(
        command="exploit-poc", target_url=url,
        passed=0 if result["verified"] else 1, failed=1 if result["verified"] else 0, total=1,
        exit_code=1 if gate else 0, started_at=started_at, duration_s=time.time() - t0,
        findings_by_severity=counts, max_severity=max_severity,
        extra={"verified": result["verified"]},
    )
    if gate:
        raise typer.Exit(code=1)


@guard_app.command(name="attack-chain")
def attack_chain(
    url: str = typer.Argument(..., help="Target URL"),
    objective: str = typer.Option(..., "--objective", help="Describe the escalation goal, e.g. 'escalate SQLi to RCE'"),
    engagement_id: str = typer.Option(..., "--engagement-id", help="Must be an 'exploit'-tier engagement"),
    max_steps: int = typer.Option(5, "--max-steps", help="Max chain steps (capped at 5)"),
    timeout_s: int = typer.Option(60, "--timeout", help="Sandbox execution timeout per step (capped at 300)"),
    fail_on: str = typer.Option("high", "--fail-on", help="Exit 1 if any finding is at/above this severity"),
) -> None:
    """Plan-and-verify a multi-step attack chain, one non-destructive sandboxed step at a time.

    Same gates as exploit-poc (exploit-tier engagement + ZYVOR_EXPLOIT_EXECUTION_ENABLED
    + a live sandbox backend) — this is exploit_poc run in a loop with an LLM planner,
    stopping the moment a step fails to verify or the planner has nothing safe left to propose.
    """
    _load_env()
    t0 = time.time()
    started_at = datetime.fromtimestamp(t0, tz=timezone.utc).isoformat()
    from agents.reporter.summary import write_ci_summary
    from orchestrator.dashboard.jobs import _job_attack_chain, _validate

    params = _validate("attack_chain", {
        "url": url, "objective": objective, "max_steps": max_steps,
        "timeout_s": timeout_s, "engagement_id": engagement_id,
    })
    result = _job_attack_chain(params)
    typer.echo(f"{result['confirmed_count']}/{len(result['steps'])} step(s) confirmed ({result['stop_reason']})")
    for step in result["steps"]:
        typer.echo(f"  step {step['step']}: {'✓' if step['verified'] else '✗'} {step['description']}")
    counts, max_severity = _findings_severity_summary(result.get("findings") or [])
    gate = _exceeds_fail_on(max_severity, fail_on)
    write_ci_summary(
        command="attack-chain", target_url=url,
        passed=result["confirmed_count"], failed=len(result["steps"]) - result["confirmed_count"],
        total=len(result["steps"]) or 1,
        exit_code=1 if gate else 0, started_at=started_at, duration_s=time.time() - t0,
        findings_by_severity=counts, max_severity=max_severity,
        extra={"stop_reason": result["stop_reason"]},
    )
    if gate:
        raise typer.Exit(code=1)


@guard_app.command(name="host-pentest")
def host_pentest(
    host: str = typer.Argument(..., help="Bare hostname or IP, e.g. host.example.com"),
    finding_description: str = typer.Option(..., "--finding", help="Describe what to verify over SSH"),
    creds_json: str = typer.Option(..., "--creds", help='JSON creds dict, e.g. \'{"username":"admin","password":{"$secret":"env:SSH_PW"}}\''),
    engagement_id: str = typer.Option(..., "--engagement-id", help="Must be an 'exploit'-tier engagement"),
    port: int = typer.Option(22, help="SSH port"),
    timeout_s: int = typer.Option(60, "--timeout", help="Sandbox execution timeout in seconds (capped at 300)"),
    fail_on: str = typer.Option("high", "--fail-on", help="Exit 1 if any finding is at/above this severity"),
) -> None:
    """Generate a non-destructive SSH verification PoC via LLM and run it sandboxed (paramiko).

    Requires ZYVOR_EXPLOIT_EXECUTION_ENABLED=true, ZYVOR_CREDENTIALED_PENTEST_ENABLED=true,
    ZYVOR_SANDBOX_HOST_IMAGE (a sandbox image with paramiko installed), and an
    exploit-tier engagement — see docs/enterprise-v2.md. Secrets in --creds must
    use {"$secret": "env:NAME"} references, never raw values.
    """
    _load_env()
    import json as _json

    t0 = time.time()
    started_at = datetime.fromtimestamp(t0, tz=timezone.utc).isoformat()
    from agents.reporter.summary import write_ci_summary
    from orchestrator.dashboard.jobs import _job_host_pentest, _validate

    try:
        creds = _json.loads(creds_json)
    except _json.JSONDecodeError as exc:
        typer.echo(f"--creds is not valid JSON: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    params = _validate("host_pentest", {
        "host": host, "port": port, "finding_description": finding_description,
        "creds": creds, "timeout_s": timeout_s, "engagement_id": engagement_id,
    })
    result = _job_host_pentest(params)
    typer.echo(f"{'VERIFIED' if result['verified'] else 'not verified'}" + (f" — {result['reason']}" if result['reason'] else ""))
    typer.echo(f"PoC: {result['poc_path']} (sha256 {result['code_sha256'][:12]}…)")
    counts, max_severity = _findings_severity_summary(result.get("findings") or [])
    gate = _exceeds_fail_on(max_severity, fail_on)
    write_ci_summary(
        command="host-pentest", target_url=host,
        passed=0 if result["verified"] else 1, failed=1 if result["verified"] else 0, total=1,
        exit_code=1 if gate else 0, started_at=started_at, duration_s=time.time() - t0,
        findings_by_severity=counts, max_severity=max_severity,
        extra={"verified": result["verified"]},
    )
    if gate:
        raise typer.Exit(code=1)


@guard_app.command(name="cloud-pentest")
def cloud_pentest(
    target: str = typer.Argument(..., help="Account/project identifier, e.g. aws-prod-123456789012"),
    provider: str = typer.Option(..., "--provider", help="'aws', 'gcp', or 'azure'"),
    finding_description: str = typer.Option(..., "--finding", help="Describe what to verify"),
    creds_json: str = typer.Option(..., "--creds", help='JSON creds dict, e.g. \'{"secret_access_key":{"$secret":"env:AWS_SECRET"}}\''),
    engagement_id: str = typer.Option(..., "--engagement-id", help="Must be an 'exploit'-tier engagement"),
    timeout_s: int = typer.Option(60, "--timeout", help="Sandbox execution timeout in seconds (capped at 300)"),
    fail_on: str = typer.Option("high", "--fail-on", help="Exit 1 if any finding is at/above this severity"),
) -> None:
    """Generate a non-destructive cloud-CLI verification PoC via LLM and run it sandboxed.

    Requires ZYVOR_EXPLOIT_EXECUTION_ENABLED=true, ZYVOR_CREDENTIALED_PENTEST_ENABLED=true,
    ZYVOR_SANDBOX_CLOUD_IMAGE (a sandbox image with the aws/gcloud/az CLIs installed),
    and an exploit-tier engagement — see docs/enterprise-v2.md. Secrets in --creds
    must use {"$secret": "env:NAME"} references, never raw values.
    """
    _load_env()
    import json as _json

    t0 = time.time()
    started_at = datetime.fromtimestamp(t0, tz=timezone.utc).isoformat()
    from agents.reporter.summary import write_ci_summary
    from orchestrator.dashboard.jobs import _job_cloud_pentest, _validate

    try:
        creds = _json.loads(creds_json)
    except _json.JSONDecodeError as exc:
        typer.echo(f"--creds is not valid JSON: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    params = _validate("cloud_pentest", {
        "provider": provider, "target": target, "finding_description": finding_description,
        "creds": creds, "timeout_s": timeout_s, "engagement_id": engagement_id,
    })
    result = _job_cloud_pentest(params)
    typer.echo(f"{'VERIFIED' if result['verified'] else 'not verified'}" + (f" — {result['reason']}" if result['reason'] else ""))
    typer.echo(f"PoC: {result['poc_path']} (sha256 {result['code_sha256'][:12]}…)")
    counts, max_severity = _findings_severity_summary(result.get("findings") or [])
    gate = _exceeds_fail_on(max_severity, fail_on)
    write_ci_summary(
        command="cloud-pentest", target_url=target,
        passed=0 if result["verified"] else 1, failed=1 if result["verified"] else 0, total=1,
        exit_code=1 if gate else 0, started_at=started_at, duration_s=time.time() - t0,
        findings_by_severity=counts, max_severity=max_severity,
        extra={"verified": result["verified"]},
    )
    if gate:
        raise typer.Exit(code=1)


@guard_app.command(name="pr-gate")
def pr_gate(
    repo: str = typer.Argument(..., help="owner/repo"),
    pr_number: int = typer.Argument(..., help="Pull request number"),
    fail_on: str = typer.Option("high", "--fail-on", help="Block the PR if any finding is at/above this severity"),
    summary_path: str = typer.Option("reports/summary.json", "--summary", help="Path to a summary.json from a prior run"),
) -> None:
    """Post a GitHub PR review + commit status from a prior run's reports/summary.json.

    Mirrors `neurosploit pr <repo> <n> --fail-on critical`: REQUEST_CHANGES + a
    failing commit status on a confirmed finding at/above --fail-on, APPROVE
    otherwise. Run the actual scan first (e.g. `argus watch audit ... --fail-on
    <sev>`) so reports/summary.json reflects this PR's code.
    """
    _load_env()
    import json as _json

    from github_integration.client import GitHubClient

    path = Path(summary_path)
    if not path.is_file():
        typer.echo(f"no summary file at {summary_path} — run a scan command first", err=True)
        raise typer.Exit(code=2)
    summary = _json.loads(path.read_text(encoding="utf-8"))
    max_severity = summary.get("max_severity")
    counts = summary.get("findings_by_severity") or {}
    gate = _exceeds_fail_on(max_severity, fail_on)

    client = GitHubClient()
    if not client.available:
        typer.echo("GitHub token required. Set GITHUB_TOKEN or run `gh auth login`.", err=True)
        raise typer.Exit(code=2)

    body_lines = [
        f"**argus security gate** — command `{summary.get('command')}` on `{summary.get('target_url')}`",
        f"Findings by severity: {counts or 'none'}",
    ]
    sha = client.get_pr_head_sha(repo, pr_number)
    if gate:
        body_lines.append(f"❌ Blocked: highest severity `{max_severity}` meets/exceeds `--fail-on {fail_on}`.")
        client.create_pr_review(repo, pr_number, event="REQUEST_CHANGES", body="\n\n".join(body_lines))
        client.set_commit_status(
            repo, sha, state="failure", context="argus/security",
            description=f"blocked: {max_severity} finding(s) present",
        )
        typer.echo(f"PR #{pr_number} blocked — {max_severity} finding(s) at/above {fail_on}")
        raise typer.Exit(code=1)

    body_lines.append("✅ No findings at/above the configured threshold.")
    client.create_pr_review(repo, pr_number, event="APPROVE", body="\n\n".join(body_lines))
    client.set_commit_status(repo, sha, state="success", context="argus/security", description="no blocking findings")
    typer.echo(f"PR #{pr_number} passed the security gate")


@app.command()
def serve(
    port: int = typer.Option(8080, help="Webhook server port"),
    host: str = typer.Option("0.0.0.0", help="Bind host"),  # nosec B104 - server must be externally reachable in Docker/K8s
    tls: bool = typer.Option(False, help="Serve over HTTPS (generates a self-signed cert if none given)"),
    tls_cert: Optional[str] = typer.Option(None, help="Path to a TLS certificate (PEM)"),
    tls_key: Optional[str] = typer.Option(None, help="Path to the TLS private key (PEM)"),
) -> None:
    """Start FastAPI webhook server for GitHub events + Mission Control dashboard."""
    _load_env()
    import uvicorn

    from orchestrator.webhook import create_app

    ssl_certfile: Optional[str] = None
    ssl_keyfile: Optional[str] = None
    if tls or tls_cert or tls_key:
        ssl_certfile, ssl_keyfile = _ensure_tls_cert(tls_cert, tls_key, host)
        typer.echo(f"Starting HTTPS server on {host}:{port} (cert: {ssl_certfile})")
    else:
        typer.echo(f"Starting webhook server on {host}:{port}")
    uvicorn.run(create_app(), host=host, port=port, ssl_certfile=ssl_certfile, ssl_keyfile=ssl_keyfile)


def _ensure_tls_cert(cert: Optional[str], key: Optional[str], host: str) -> tuple[str, str]:
    """Return (cert_path, key_path); generate a self-signed pair if not provided."""
    import subprocess

    if cert and key:
        return cert, key
    cert_dir = Path.home() / ".zyvor-argus" / "tls"
    cert_dir.mkdir(parents=True, exist_ok=True)
    cert_path, key_path = cert_dir / "server.crt", cert_dir / "server.key"
    if cert_path.exists() and key_path.exists():
        return str(cert_path), str(key_path)
    cn = host if host not in ("0.0.0.0", "") else "localhost"  # nosec B104 - cert CN choice, not a bind address
    typer.echo(f"Generating self-signed TLS certificate (CN={cn}) → {cert_dir}")
    subprocess.run(
        [
            "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
            "-keyout", str(key_path), "-out", str(cert_path),
            "-days", "825", "-subj", f"/CN={cn}",
            "-addext", f"subjectAltName=DNS:{cn},DNS:localhost,IP:127.0.0.1",
        ],
        check=True, capture_output=True,
    )
    return str(cert_path), str(key_path)


@ask_app.command("ingest")
def knowledge_ingest(
    path: Path = typer.Argument(..., help="File or directory to ingest"),
    tenant_id: str = typer.Option("public", "--tenant-id"),
    access_level: str = typer.Option("public", "--access-level"),
    product: Optional[str] = typer.Option(None, "--product"),
    source: str = typer.Option("documentation", "--source"),
    chunk_size: int = typer.Option(1400, "--chunk-size"),
    chunk_overlap: int = typer.Option(180, "--chunk-overlap"),
    batch_size: int = typer.Option(64, "--batch-size"),
) -> None:
    """Ingest docs into the Zyvor knowledge Qdrant collection (requires [knowledge])."""
    _load_env()
    try:
        from scripts.knowledge_ingest import main as ingest_main
    except ImportError as exc:
        typer.echo(
            "Knowledge extras missing. Install with: pip install -e '.[knowledge]'",
            err=True,
        )
        raise typer.Exit(code=1) from exc

    import sys

    argv = [
        str(path),
        "--tenant-id",
        tenant_id,
        "--access-level",
        access_level,
        "--source",
        source,
        "--chunk-size",
        str(chunk_size),
        "--chunk-overlap",
        str(chunk_overlap),
        "--batch-size",
        str(batch_size),
    ]
    if product:
        argv.extend(["--product", product])
    sys.argv = ["knowledge-ingest", *argv]
    ingest_main()


@ask_app.command("evaluate")
def knowledge_evaluate(
    base_url: str = typer.Option("http://localhost:8080", "--base-url"),
    api_key: Optional[str] = typer.Option(None, "--api-key"),
    tenant_id: str = typer.Option("public", "--tenant-id"),
    dataset: Path = typer.Option(
        Path("eval/knowledge_questions.jsonl"), "--dataset"
    ),
    output: Path = typer.Option(Path("eval/knowledge_report.json"), "--output"),
) -> None:
    """Evaluate a running knowledge QA API against the sample dataset."""
    _load_env()
    import sys

    from scripts.knowledge_evaluate import main as evaluate_main

    argv = [
        "--base-url",
        base_url,
        "--tenant-id",
        tenant_id,
        "--dataset",
        str(dataset),
        "--output",
        str(output),
    ]
    if api_key:
        argv.extend(["--api-key", api_key])
    sys.argv = ["knowledge-evaluate", *argv]
    evaluate_main()


legacy_app = typer.Typer(
    name="zyvor-qa",
    help="Zyvor Argus (deprecated legacy flat CLI — use `argus` instead)",
    no_args_is_help=True,
)
legacy_app.command("run")(run)
legacy_app.command("test")(test)
legacy_app.command("generate")(generate)
legacy_app.command("discover")(discover)
legacy_app.command("create")(create)
legacy_app.command("regression")(regression)
legacy_app.command("flow")(flow)
legacy_app.command("route-sweep")(route_sweep)
legacy_app.command("api-test")(api_test)
legacy_app.command("ai-test")(ai_test)
legacy_app.command("auth-test")(auth_test)
legacy_app.command("har-replay")(har_replay)
legacy_app.command("import-codegen")(import_codegen_cmd)
legacy_app.command("realtime")(realtime)
legacy_app.command("vitals")(vitals)
legacy_app.command("audit")(audit)
legacy_app.command("misconfig-scan")(misconfig_scan)
legacy_app.command("cve-lookup")(cve_lookup)
legacy_app.command("llm-redteam")(llm_redteam)
legacy_app.command("exploit-poc")(exploit_poc)
legacy_app.command("attack-chain")(attack_chain)
legacy_app.command("host-pentest")(host_pentest)
legacy_app.command("cloud-pentest")(cloud_pentest)
legacy_app.command("pr-gate")(pr_gate)
legacy_app.command("serve")(serve)
legacy_app.command("knowledge-ingest")(knowledge_ingest)
legacy_app.command("knowledge-evaluate")(knowledge_evaluate)


if __name__ == "__main__":
    app()


def main() -> None:
    app()


def legacy_main() -> None:
    typer.echo(
        "warning: `zyvor-qa` is deprecated and will be removed in a future release; use `argus` instead.",
        err=True,
    )
    legacy_app()

