# Copyright 2026 Zyvor AI Labs · https://zyvor.dev
# SPDX-License-Identifier: LicenseRef-Zyvor-Production-1.0
"""Read-only Kubernetes inspector for the Mission Control dashboard.

Every public function degrades to an ``{"available": False}`` payload instead of
raising, so the dashboard works identically in-cluster, with a local kubeconfig,
or with no cluster at all.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

NAMESPACE_FILE = Path("/var/run/secrets/kubernetes.io/serviceaccount/namespace")

_client_cache: dict[str, Any] = {}
_log = logging.getLogger(__name__)


def _client_error(exc: BaseException) -> str:
    """Log the real failure server-side; return a generic client-facing string."""
    _log.warning("kubernetes client error: %s", exc)
    return "cluster query failed"


def _load_clients() -> Optional[dict[str, Any]]:
    """Return cached API clients, or None when no cluster is reachable."""
    if "clients" in _client_cache:
        return _client_cache["clients"]

    # Imported via importlib: the repo's kubernetes/ manifest directory can shadow
    # the installed client package when cwd is on sys.path.
    import importlib

    try:
        client = importlib.import_module("kubernetes.client")
        config = importlib.import_module("kubernetes.config")
    except ImportError:
        _client_cache["clients"] = None
        return None

    try:
        config.load_incluster_config()
    except Exception:
        try:
            config.load_kube_config()
        except Exception:
            _client_cache["clients"] = None
            return None

    clients = {
        "core": client.CoreV1Api(),
        "apps": client.AppsV1Api(),
        "batch": client.BatchV1Api(),
        "custom": client.CustomObjectsApi(),
    }
    _client_cache["clients"] = clients
    return clients


def _parse_cpu(raw: str) -> float:
    """Kubernetes CPU quantity → millicores."""
    raw = raw.strip()
    try:
        if raw.endswith("n"):
            return float(raw[:-1]) / 1_000_000
        if raw.endswith("u"):
            return float(raw[:-1]) / 1_000
        if raw.endswith("m"):
            return float(raw[:-1])
        return float(raw) * 1000
    except ValueError:
        return 0.0


def _parse_mem(raw: str) -> int:
    """Kubernetes memory quantity → bytes."""
    raw = raw.strip()
    units = {"Ki": 1024, "Mi": 1024**2, "Gi": 1024**3, "Ti": 1024**4, "K": 1000, "M": 1000**2, "G": 1000**3}
    for suffix, mult in units.items():
        if raw.endswith(suffix):
            try:
                return int(float(raw[: -len(suffix)]) * mult)
            except ValueError:
                return 0
    try:
        return int(raw)
    except ValueError:
        return 0


def _pod_metrics(clients: dict[str, Any], namespace: str) -> dict[str, dict[str, Any]]:
    """Pod name → {cpu_millicores, memory_bytes} via metrics-server (best effort)."""
    usage: dict[str, dict[str, Any]] = {}
    try:
        data = clients["custom"].list_namespaced_custom_object(
            "metrics.k8s.io", "v1beta1", namespace, "pods"
        )
    except Exception:
        return usage
    for item in data.get("items", []):
        name = item.get("metadata", {}).get("name")
        if not name:
            continue
        cpu = sum(_parse_cpu(c.get("usage", {}).get("cpu", "0")) for c in item.get("containers", []))
        mem = sum(_parse_mem(c.get("usage", {}).get("memory", "0")) for c in item.get("containers", []))
        usage[name] = {"cpu_millicores": round(cpu, 1), "memory_bytes": mem}
    return usage


def reset_client_cache() -> None:
    """Drop cached clients (used by tests and after kubeconfig changes)."""
    _client_cache.clear()


def get_namespace() -> str:
    """Resolve the namespace to inspect."""
    env_ns = os.environ.get("DASHBOARD_NAMESPACE", "").strip()
    if env_ns:
        return env_ns
    if NAMESPACE_FILE.exists():
        try:
            return NAMESPACE_FILE.read_text(encoding="utf-8").strip() or "default"
        except OSError:
            pass
    return "default"


def _pod_selector() -> Optional[str]:
    selector = os.environ.get("DASHBOARD_POD_SELECTOR", "").strip()
    return selector or None


def _age_seconds(start: Optional[datetime]) -> Optional[int]:
    if not start:
        return None
    return max(0, int((datetime.now(timezone.utc) - start).total_seconds()))


def _pod_restart_count(pod: Any) -> int:
    statuses = pod.status.container_statuses or []
    return sum(s.restart_count or 0 for s in statuses)


def _pod_ready(pod: Any) -> tuple[int, int]:
    statuses = pod.status.container_statuses or []
    total = len(pod.spec.containers or [])
    ready = sum(1 for s in statuses if s.ready)
    return ready, total


def _pod_images(pod: Any) -> list[str]:
    return [c.image for c in (pod.spec.containers or [])]


def list_pods() -> dict[str, Any]:
    """List pods in the dashboard namespace with health details."""
    clients = _load_clients()
    namespace = get_namespace()
    if not clients:
        return {"available": False, "namespace": namespace, "pods": []}

    try:
        result = clients["core"].list_namespaced_pod(
            namespace,
            label_selector=_pod_selector(),
        )
        warnings = _recent_warning_events(clients, namespace)
    except Exception as exc:
        return {"available": False, "namespace": namespace, "pods": [], "error": _client_error(exc)}

    metrics = _pod_metrics(clients, namespace)

    pods: list[dict[str, Any]] = []
    for pod in result.items:
        ready, total = _pod_ready(pod)
        name = pod.metadata.name
        pods.append(
            {
                "name": name,
                "phase": pod.status.phase or "Unknown",
                "ready": ready,
                "total": total,
                "restarts": _pod_restart_count(pod),
                "age_seconds": _age_seconds(pod.status.start_time),
                "node": pod.spec.node_name,
                "pod_ip": pod.status.pod_ip,
                "images": _pod_images(pod),
                "warnings": warnings.get(name, []),
                "usage": metrics.get(name),
            }
        )

    pods.sort(key=lambda p: p["name"])
    return {"available": True, "namespace": namespace, "pods": pods}


def _recent_warning_events(clients: dict[str, Any], namespace: str) -> dict[str, list[str]]:
    """Map pod name -> recent Warning event messages (best effort)."""
    warnings: dict[str, list[str]] = {}
    try:
        events = clients["core"].list_namespaced_event(
            namespace,
            field_selector="type=Warning",
        )
    except Exception:
        return warnings

    for event in events.items[-100:]:
        involved = event.involved_object
        if involved and involved.kind == "Pod" and involved.name:
            message = f"{event.reason}: {event.message or ''}".strip()
            warnings.setdefault(involved.name, []).append(message[:200])
    return {name: msgs[-3:] for name, msgs in warnings.items()}


def _normalize_log_text(raw: Any) -> str:
    """Undo the kubernetes client's occasional str(bytes) mangling of pod logs."""
    if isinstance(raw, bytes):
        return raw.decode("utf-8", "replace")
    text = str(raw)
    if text.startswith(("b'", 'b"')) and text.endswith(("'", '"')):
        import ast

        try:
            decoded = ast.literal_eval(text)
            if isinstance(decoded, bytes):
                return decoded.decode("utf-8", "replace")
        except (ValueError, SyntaxError):
            pass
    return text


def pod_logs(name: str, lines: int = 100, container: Optional[str] = None) -> dict[str, Any]:
    """Return the log tail for a pod.

    Multi-container pods (e.g. KubeVirt virt-launcher) require an explicit
    container name — when none is given, tail every container with a header
    separating each section.
    """
    clients = _load_clients()
    namespace = get_namespace()
    if not clients:
        return {"available": False, "name": name, "lines": []}

    tail = max(1, min(lines, 1000))

    containers: list[str] = []
    if container:
        containers = [container]
    else:
        try:
            pod = clients["core"].read_namespaced_pod(name, namespace)
            containers = [c.name for c in (pod.spec.containers or [])]
        except Exception:
            containers = []

    out: list[str] = []
    fetched = 0
    last_error: Optional[str] = None
    names_to_fetch: list[Optional[str]] = list(containers) if containers else [None]
    for cname in names_to_fetch:
        try:
            raw = clients["core"].read_namespaced_pod_log(
                name,
                namespace,
                container=cname,
                tail_lines=tail,
                timestamps=True,
            )
            raw = _normalize_log_text(raw)
        except Exception as exc:
            last_error = _client_error(exc)
            if len(containers) > 1:
                out.append(f"────── container: {cname} — logs unavailable ──────")
            continue
        if len(containers) > 1:
            out.append(f"────── container: {cname} ──────")
        out.extend(raw.splitlines())
        fetched += 1

    if fetched == 0:
        return {"available": False, "name": name, "lines": [], "error": last_error or "no logs"}

    return {
        "available": True,
        "name": name,
        "containers": containers,
        "lines": out,
    }


def delete_pod(name: str) -> dict[str, Any]:
    """Delete a pod (its Deployment/CronJob recreates it — i.e. a restart)."""
    clients = _load_clients()
    namespace = get_namespace()
    if not clients:
        return {"ok": False, "error": "cluster unavailable"}
    try:
        clients["core"].delete_namespaced_pod(name, namespace)
    except Exception as exc:
        return {"ok": False, "error": _client_error(exc)}
    return {"ok": True, "name": name}


def recent_events(limit: int = 25) -> dict[str, Any]:
    """Recent namespace events, newest first (best effort)."""
    clients = _load_clients()
    namespace = get_namespace()
    if not clients:
        return {"available": False, "events": []}
    try:
        result = clients["core"].list_namespaced_event(namespace)
    except Exception as exc:
        return {"available": False, "events": [], "error": _client_error(exc)}

    events = []
    for ev in result.items:
        when = ev.last_timestamp or ev.event_time or (ev.metadata.creation_timestamp if ev.metadata else None)
        events.append(
            {
                "type": ev.type,
                "reason": ev.reason,
                "object": f"{ev.involved_object.kind}/{ev.involved_object.name}" if ev.involved_object else "",
                "message": (ev.message or "")[:200],
                "count": ev.count or 1,
                "at": when.isoformat() if when else None,
            }
        )
    events.sort(key=lambda e: e["at"] or "", reverse=True)
    return {"available": True, "events": events[:limit]}


def get_workloads() -> dict[str, Any]:
    """Deployment replica health and CronJob schedule status."""
    clients = _load_clients()
    namespace = get_namespace()
    if not clients:
        return {"available": False, "namespace": namespace, "deployments": [], "cronjobs": []}

    deployments: list[dict[str, Any]] = []
    cronjobs: list[dict[str, Any]] = []

    try:
        for dep in clients["apps"].list_namespaced_deployment(namespace).items:
            deployments.append(
                {
                    "name": dep.metadata.name,
                    "ready": dep.status.ready_replicas or 0,
                    "desired": dep.spec.replicas or 0,
                }
            )
        for cron in clients["batch"].list_namespaced_cron_job(namespace).items:
            last = cron.status.last_schedule_time
            last_success = cron.status.last_successful_time
            cronjobs.append(
                {
                    "name": cron.metadata.name,
                    "schedule": cron.spec.schedule,
                    "suspend": bool(cron.spec.suspend),
                    "last_schedule": last.isoformat() if last else None,
                    "last_successful": last_success.isoformat() if last_success else None,
                    "active": len(cron.status.active or []),
                }
            )
    except Exception as exc:
        return {
            "available": False,
            "namespace": namespace,
            "deployments": deployments,
            "cronjobs": cronjobs,
            "error": _client_error(exc),
        }

    return {
        "available": True,
        "namespace": namespace,
        "deployments": deployments,
        "cronjobs": cronjobs,
    }
