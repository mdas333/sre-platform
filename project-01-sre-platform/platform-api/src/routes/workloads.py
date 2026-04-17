"""
Workloads routes — the developer-facing Platform API surface.

Create, list, fetch, scale, query health, and get SLO status per workload.
Mutating operations emit signed audit receipts.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from k8s.workloads import list_deployments
from slo.model import (
    SLO,
    SLOState,
    burn_rate,
    error_budget_remaining,
    error_budget_total,
    health_state,
)
from slo.store import SLOStore

from .state import get_emitter, get_slo_store

router = APIRouter()


class WorkloadCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=63)
    image: str
    replicas: int = Field(1, ge=0, le=50)
    slo_target: float = Field(99.9, gt=0, le=100)
    slo_window_seconds: int = Field(7 * 86400, gt=0)
    slo_indicator: str = "http_success_rate"


class WorkloadScale(BaseModel):
    replicas: int = Field(..., ge=0, le=50)


def _slo_view(store: SLOStore, workload_id: str) -> dict | None:
    entry = store.get(workload_id)
    if not entry:
        return None
    s: SLOState = entry.state()
    return {
        "target": entry.slo.target,
        "window_seconds": entry.slo.window_seconds,
        "indicator": entry.slo.indicator,
        "total_events": s.total_events,
        "failed_events": s.failed_events,
        "elapsed_seconds": s.elapsed_seconds,
        "error_budget_total": round(error_budget_total(entry.slo, s), 3),
        "error_budget_remaining": round(error_budget_remaining(entry.slo, s), 3),
        "burn_rate": round(burn_rate(entry.slo, s), 3),
        "state": health_state(entry.slo, s),
    }


@router.post("/workloads", status_code=201)
def create_workload(body: WorkloadCreate) -> dict:
    store = get_slo_store()
    if store.get(body.name) is not None:
        raise HTTPException(status_code=409, detail=f"workload {body.name!r} already exists")
    slo = SLO(
        target=body.slo_target,
        window_seconds=body.slo_window_seconds,
        indicator=body.slo_indicator,
    )
    store.register(body.name, slo)
    emitter = get_emitter()
    receipt = emitter.emit(
        action="create",
        workload_id=body.name,
        before=None,
        after={"image": body.image, "replicas": body.replicas},
    )
    return {"workload_id": body.name, "slo": _slo_view(store, body.name), "receipt": receipt}


@router.get("/workloads")
def list_workloads() -> dict:
    store = get_slo_store()
    return {"count": len(store.list()), "workloads": [w.workload_id for w in store.list()]}


@router.get("/workloads/{workload_id}")
def get_workload(workload_id: str) -> dict:
    view = _slo_view(get_slo_store(), workload_id)
    if view is None:
        raise HTTPException(status_code=404, detail="workload not found")
    return {"workload_id": workload_id, "slo": view}


@router.get("/workloads/{workload_id}/health")
def workload_health(workload_id: str) -> dict:
    view = _slo_view(get_slo_store(), workload_id)
    if view is None:
        raise HTTPException(status_code=404, detail="workload not found")
    return {"workload_id": workload_id, "state": view["state"]}


@router.get("/workloads/{workload_id}/slo")
def workload_slo(workload_id: str) -> dict:
    view = _slo_view(get_slo_store(), workload_id)
    if view is None:
        raise HTTPException(status_code=404, detail="workload not found")
    return view


@router.post("/workloads/{workload_id}/scale")
def workload_scale(workload_id: str, body: WorkloadScale) -> dict:
    store = get_slo_store()
    if store.get(workload_id) is None:
        raise HTTPException(status_code=404, detail="workload not found")

    # Best-effort observed state from the cluster (may be empty in dev).
    observed = [d for d in list_deployments("sre-platform") if d.get("name") == workload_id]
    before_reps = observed[0]["desired"] if observed else None

    receipt = get_emitter().emit(
        action="scale",
        workload_id=workload_id,
        before={"replicas": before_reps} if before_reps is not None else {},
        after={"replicas": body.replicas},
    )
    return {"workload_id": workload_id, "scaled_to": body.replicas, "receipt": receipt}
