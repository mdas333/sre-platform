"""Health routes — pod probes and aggregate cluster health score."""

from __future__ import annotations

from fastapi import APIRouter

from k8s.nodes import count_ready_nodes, list_nodes
from k8s.workloads import list_deployments, list_pods

router = APIRouter()


@router.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@router.get("/readyz")
def readyz() -> dict:
    return {"status": "ready"}


@router.get("/cluster/health")
def cluster_health() -> dict:
    """
    Aggregate 0–100 cluster health score.

    Mix:
      40 pts — node readiness
      30 pts — pod Running ratio in the platform namespace
      20 pts — deployment availability
      10 pts — absence of recent warnings (reserved; 10 points always awarded if no events scan is available)
    """
    nodes = list_nodes()
    ready, total = count_ready_nodes(nodes)
    node_pts = 40 * (ready / total) if total else 0.0

    pods = list_pods("sre-platform")
    running = sum(1 for p in pods if p.get("phase") == "Running")
    pod_pts = 30 * (running / len(pods)) if pods else 30.0

    deps = list_deployments("sre-platform")
    if deps:
        avail = sum(
            1 for d in deps if d.get("available") and d.get("available") >= d.get("desired", 0)
        )
        dep_pts = 20 * (avail / len(deps))
    else:
        dep_pts = 20.0

    # Events-penalty: reserved pending SigNoz log query integration.
    event_pts = 10.0

    score = round(node_pts + pod_pts + dep_pts + event_pts, 1)

    return {
        "score": score,
        "breakdown": {
            "nodes": {"points": round(node_pts, 1), "ready": ready, "total": total},
            "pods": {"points": round(pod_pts, 1), "running": running, "total": len(pods)},
            "deployments": {"points": round(dep_pts, 1), "total": len(deps)},
            "events": {"points": event_pts},
        },
    }
