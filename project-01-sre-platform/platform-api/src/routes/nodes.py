"""Node listing route."""

from __future__ import annotations

from fastapi import APIRouter

from k8s.nodes import list_nodes

router = APIRouter()


@router.get("/cluster/nodes")
def cluster_nodes() -> dict:
    nodes = list_nodes()
    return {"count": len(nodes), "nodes": nodes}
