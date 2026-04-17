"""Node queries."""

from __future__ import annotations

import logging

from .client import core_v1, ensure_loaded

logger = logging.getLogger(__name__)


def list_nodes() -> list[dict]:
    """Return a compact per-node status list, or [] if cluster is unreachable."""
    if not ensure_loaded():
        return []
    try:
        nodes = core_v1().list_node()
    except Exception:
        logger.exception("failed to list nodes")
        return []

    out: list[dict] = []
    for n in nodes.items:
        conditions = {c.type: c.status for c in (n.status.conditions or [])}
        out.append(
            {
                "name": n.metadata.name,
                "ready": conditions.get("Ready") == "True",
                "roles": [
                    k.split("/")[-1]
                    for k in (n.metadata.labels or {})
                    if k.startswith("node-role.kubernetes.io/")
                ]
                or ["worker"],
                "kubelet_version": n.status.node_info.kubelet_version,
                "cpu_capacity": n.status.capacity.get("cpu"),
                "memory_capacity": n.status.capacity.get("memory"),
                "conditions": conditions,
            }
        )
    return out


def count_ready_nodes(nodes: list[dict]) -> tuple[int, int]:
    total = len(nodes)
    ready = sum(1 for n in nodes if n.get("ready"))
    return ready, total
