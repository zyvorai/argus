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

"""Sandboxed execution for LLM-generated exploit/PoC code.

Real containment, not a convenience wrapper: code from the `exploit_poc` job
kind runs in a short-lived Kubernetes Job (see `kubernetes/sandbox.yaml`) —
dropped capabilities, non-root, read-only rootfs, no token automount,
resource limits, a hard wall-clock timeout — never inside the job-runner
process itself. If no cluster is reachable, or the dedicated sandbox
namespace isn't explicitly configured, execution is refused
(`SandboxUnavailable`) rather than silently falling back to running
generated code unsandboxed.

Per-Job network-egress restriction is attempted (a NetworkPolicy scoped to
the resolved IPs of the engagement's target) but is best-effort, not the
primary boundary — see `kubernetes/sandbox.yaml`'s CNI caveat. The pod
security hardening is what actually holds on every CNI.
"""

from __future__ import annotations

import os
import socket
import time
import uuid
from dataclasses import dataclass
from typing import Any

_DEFAULT_IMAGE = "python:3.12-slim"


class SandboxUnavailable(RuntimeError):
    """No usable sandbox backend is configured/reachable."""


@dataclass(frozen=True)
class SandboxResult:
    exit_code: int | None
    stdout: str
    timed_out: bool
    network_policy_applied: bool


def _sandbox_namespace() -> str | None:
    ns = os.environ.get("ZYVOR_SANDBOX_NAMESPACE", "").strip()
    return ns or None


def _sandbox_service_account() -> str:
    return os.environ.get("ZYVOR_SANDBOX_SERVICE_ACCOUNT", "argus-sandbox").strip() or "argus-sandbox"


def _sandbox_image() -> str:
    return os.environ.get("ZYVOR_SANDBOX_IMAGE", _DEFAULT_IMAGE).strip() or _DEFAULT_IMAGE


def host_pentest_image() -> str | None:
    """Image for `host_pentest` (needs `paramiko` — not in the default
    image). None if not configured — host_pentest fails closed rather than
    running with a generic image that lacks SSH tooling."""
    return os.environ.get("ZYVOR_SANDBOX_HOST_IMAGE", "").strip() or None


def cloud_pentest_image() -> str | None:
    """Image for `cloud_pentest` (needs the `aws`/`gcloud`/`az` CLIs — not
    in the default image). None if not configured — cloud_pentest fails
    closed rather than running with a generic image that lacks them."""
    return os.environ.get("ZYVOR_SANDBOX_CLOUD_IMAGE", "").strip() or None


def db_image() -> str | None:
    """Image for `db_assert` (needs `psycopg`/`pymysql` — not in the default
    image; sqlite3 is stdlib but the same image serves all three engines,
    simpler than one image per engine). None if not configured —
    db_assert fails closed rather than running with a generic image that
    lacks database drivers."""
    return os.environ.get("ZYVOR_SANDBOX_DB_IMAGE", "").strip() or None


def chaos_image() -> str | None:
    """Image for `chaos_inject` (needs `iproute2`/`iptables` — not in the
    default image). None if not configured — chaos_inject fails closed
    rather than running with a generic image that lacks fault-injection
    tooling."""
    return os.environ.get("ZYVOR_SANDBOX_CHAOS_IMAGE", "").strip() or None


def available() -> bool:
    """True when a cluster is reachable AND a dedicated sandbox namespace is
    explicitly configured. The namespace requirement is deliberate: refusing
    to default to the app's own namespace prevents an unconfigured
    deployment from silently running generated code next to production
    workloads."""
    if not _sandbox_namespace():
        return False
    from orchestrator.dashboard.k8s import _load_clients

    return _load_clients() is not None


def _resolve_egress_cidrs(hosts: list[str]) -> list[str]:
    cidrs: list[str] = []
    for host in hosts:
        try:
            for info in socket.getaddrinfo(host, None):
                ip = str(info[4][0])
                if ":" not in ip and f"{ip}/32" not in cidrs:  # IPv4 only for this pass
                    cidrs.append(f"{ip}/32")
        except socket.gaierror:
            continue
    return cidrs


def _apply_egress_policy(client: Any, clients: dict[str, Any], namespace: str, job_name: str, hosts: list[str]) -> bool:
    """Best-effort — see module docstring's CNI caveat. Never raises;
    returns whether it believes the policy object was created."""
    cidrs = _resolve_egress_cidrs(hosts)
    if not cidrs:
        return False
    try:
        networking = client.NetworkingV1Api(clients["core"].api_client)
        egress_rules = [
            client.V1NetworkPolicyEgressRule(
                ports=[
                    client.V1NetworkPolicyPort(protocol="UDP", port=53),
                    client.V1NetworkPolicyPort(protocol="TCP", port=53),
                ]
            ),
        ] + [
            client.V1NetworkPolicyEgressRule(
                to=[client.V1NetworkPolicyPeer(ip_block=client.V1IPBlock(cidr=cidr))]
            )
            for cidr in cidrs
        ]
        policy = client.V1NetworkPolicy(
            metadata=client.V1ObjectMeta(name=f"{job_name}-egress"),
            spec=client.V1NetworkPolicySpec(
                pod_selector=client.V1LabelSelector(match_labels={"job-name": job_name}),
                policy_types=["Egress"],
                egress=egress_rules,
            ),
        )
        networking.create_namespaced_network_policy(namespace, policy)
        return True
    except Exception:
        return False


def run_python(
    code: str,
    *,
    timeout_s: int = 60,
    env: dict[str, str] | None = None,
    egress_hosts: list[str] | None = None,
    image: str | None = None,
) -> SandboxResult:
    """Run `code` as a one-shot Job in the sandbox namespace.

    `image` overrides the default `ZYVOR_SANDBOX_IMAGE` — used by job kinds
    that need tooling the default `python:3.12-slim` doesn't have (e.g.
    `host_pentest`'s `paramiko`, `cloud_pentest`'s `aws`/`gcloud`/`az` CLIs).
    `env` is the one place secret VALUES ever appear — they go straight into
    the ephemeral Job's container env, never into `code` or any persisted
    record; callers must resolve `{"$secret": ...}` references before
    calling this, and must never log the resolved values themselves.

    Raises SandboxUnavailable if no sandbox backend is configured/reachable
    — callers must not fall back to any other execution path on this error."""
    return _run_job(code, timeout_s=timeout_s, env=env, egress_hosts=egress_hosts, image=image, extra_capabilities=None)


def run_chaos(
    code: str,
    *,
    timeout_s: int = 60,
    env: dict[str, str] | None = None,
    egress_hosts: list[str] | None = None,
    image: str | None = None,
) -> SandboxResult:
    """Like `run_python()`, but grants `CAP_NET_ADMIN` — needed for `tc`/
    `iptables` fault-shaping inside the pod's own network namespace.

    This is a deliberate, narrow exception to the sandbox's normal "drop ALL
    capabilities" invariant — every other kind (`exploit_poc`, `host_pentest`,
    `cloud_pentest`, `db_assert`, ...) runs with capabilities fully dropped.
    Reachable ONLY from `_job_chaos_inject` — never the generic PoC path.
    Same non-root/read-only-rootfs/no-ServiceAccount-token/resource-limits/
    timeout hardening as `run_python()` otherwise; only the capability set
    differs. See `kubernetes/sandbox.yaml` for the full caveat, and
    `ROADMAP.md`'s chaos-testing section for why this exception exists."""
    return _run_job(
        code, timeout_s=timeout_s, env=env, egress_hosts=egress_hosts, image=image,
        extra_capabilities=["NET_ADMIN"],
    )


def _run_job(
    code: str,
    *,
    timeout_s: int,
    env: dict[str, str] | None,
    egress_hosts: list[str] | None,
    image: str | None,
    extra_capabilities: list[str] | None,
) -> SandboxResult:
    if not available():
        raise SandboxUnavailable(
            "no sandbox backend available — set ZYVOR_SANDBOX_NAMESPACE to a "
            "dedicated namespace (see kubernetes/sandbox.yaml) and ensure the "
            "cluster is reachable"
        )

    import importlib

    client = importlib.import_module("kubernetes.client")
    from orchestrator.dashboard.k8s import _load_clients

    clients = _load_clients()
    assert clients is not None  # available() already checked this
    namespace = _sandbox_namespace()
    assert namespace is not None

    job_name = f"zyvor-poc-{uuid.uuid4().hex[:12]}"
    configmap_name = f"{job_name}-code"
    timeout_s = max(5, min(timeout_s, 300))

    clients["core"].create_namespaced_config_map(
        namespace,
        client.V1ConfigMap(metadata=client.V1ObjectMeta(name=configmap_name), data={"poc.py": code}),
    )

    network_policy_applied = False
    if egress_hosts:
        network_policy_applied = _apply_egress_policy(client, clients, namespace, job_name, egress_hosts)

    security_context = client.V1SecurityContext(
        allow_privilege_escalation=False,
        read_only_root_filesystem=True,
        run_as_non_root=True,
        run_as_user=65534,
        capabilities=client.V1Capabilities(drop=["ALL"], add=extra_capabilities or None),
    )
    container = client.V1Container(
        name="poc",
        image=image or _sandbox_image(),
        # Kubernetes defaults to Always for ':latest'-tagged images, which
        # tries to pull from a registry even for images pre-loaded onto the
        # node (e.g. a custom host_pentest/cloud_pentest image built and
        # `ctr images import`-ed locally, never pushed anywhere) — that
        # fails with ErrImagePull. IfNotPresent uses what's already on the
        # node first, which is the common case for this sandbox.
        image_pull_policy="IfNotPresent",
        command=["python3", "/code/poc.py"],
        env=[client.V1EnvVar(name=k, value=v) for k, v in (env or {}).items()],
        security_context=security_context,
        resources=client.V1ResourceRequirements(
            requests={"cpu": "100m", "memory": "128Mi"},
            limits={"cpu": "500m", "memory": "256Mi"},
        ),
        volume_mounts=[
            client.V1VolumeMount(name="code", mount_path="/code", read_only=True),
            # This is the sandboxed container's own isolated /tmp (a size-limited
            # emptyDir, given the container's rootfs is otherwise read-only) — not
            # a reference to this host's /tmp, so bandit's B108 doesn't apply.
            client.V1VolumeMount(name="tmp", mount_path="/tmp"),  # nosec B108
        ],
    )
    pod_spec = client.V1PodSpec(
        containers=[container],
        restart_policy="Never",
        automount_service_account_token=False,
        service_account_name=_sandbox_service_account(),
        volumes=[
            client.V1Volume(name="code", config_map=client.V1ConfigMapVolumeSource(name=configmap_name)),
            client.V1Volume(name="tmp", empty_dir=client.V1EmptyDirVolumeSource(size_limit="64Mi")),
        ],
        active_deadline_seconds=timeout_s,
    )
    job = client.V1Job(
        metadata=client.V1ObjectMeta(name=job_name, labels={"app": "argus-sandbox"}),
        spec=client.V1JobSpec(
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"job-name": job_name}), spec=pod_spec
            ),
            backoff_limit=0,
            ttl_seconds_after_finished=300,
        ),
    )

    timed_out = False
    exit_code: int | None = None
    stdout = ""
    try:
        clients["batch"].create_namespaced_job(namespace, job)
        deadline = time.time() + timeout_s + 15  # grace period beyond activeDeadlineSeconds
        finished = False
        while time.time() < deadline:
            status = clients["batch"].read_namespaced_job_status(job_name, namespace).status
            if status.succeeded or status.failed:
                finished = True
                break
            time.sleep(2)
        timed_out = not finished

        pods = clients["core"].list_namespaced_pod(namespace, label_selector=f"job-name={job_name}").items
        if pods:
            from orchestrator.dashboard.k8s import _normalize_log_text

            pod_name = pods[0].metadata.name
            try:
                stdout = _normalize_log_text(clients["core"].read_namespaced_pod_log(pod_name, namespace))
            except Exception:
                stdout = ""
            statuses = pods[0].status.container_statuses or []
            if statuses and statuses[0].state.terminated:
                exit_code = statuses[0].state.terminated.exit_code
        return SandboxResult(
            exit_code=exit_code, stdout=stdout, timed_out=timed_out,
            network_policy_applied=network_policy_applied,
        )
    finally:
        try:
            clients["batch"].delete_namespaced_job(job_name, namespace, propagation_policy="Background")
        except Exception:
            pass
        try:
            clients["core"].delete_namespaced_config_map(configmap_name, namespace)
        except Exception:
            pass
        if network_policy_applied:
            try:
                networking = client.NetworkingV1Api(clients["core"].api_client)
                networking.delete_namespaced_network_policy(f"{job_name}-egress", namespace)
            except Exception:
                pass
