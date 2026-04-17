"""Workload queries (Deployments in the platform namespace)."""

from __future__ import annotations

import logging

from kubernetes.client.rest import ApiException

from .client import apps_v1, core_v1, ensure_loaded

logger = logging.getLogger(__name__)


def list_deployments(namespace: str) -> list[dict]:
    if not ensure_loaded():
        return []
    try:
        deps = apps_v1().list_namespaced_deployment(namespace=namespace)
    except ApiException:
        logger.exception("failed to list deployments in %s", namespace)
        return []
    return [
        {
            "name": d.metadata.name,
            "desired": d.spec.replicas or 0,
            "available": d.status.available_replicas or 0,
            "ready": d.status.ready_replicas or 0,
            "labels": dict(d.metadata.labels or {}),
        }
        for d in deps.items
    ]


def list_pods(namespace: str, label_selector: str | None = None) -> list[dict]:
    if not ensure_loaded():
        return []
    try:
        pods = core_v1().list_namespaced_pod(namespace=namespace, label_selector=label_selector)
    except ApiException:
        logger.exception("failed to list pods in %s", namespace)
        return []
    return [
        {
            "name": p.metadata.name,
            "phase": p.status.phase,
            "restarts": sum(
                (cs.restart_count or 0) for cs in (p.status.container_statuses or [])
            ),
            "node": p.spec.node_name,
        }
        for p in pods.items
    ]
