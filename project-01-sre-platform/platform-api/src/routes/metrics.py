"""Prometheus metrics endpoint — scraped by OTel Collector or a side-car."""

from __future__ import annotations

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Gauge, generate_latest

from slo.model import burn_rate, error_budget_remaining

from .state import get_slo_store

router = APIRouter()

_registry = CollectorRegistry()
_budget_remaining = Gauge(
    "platform_slo_error_budget_remaining",
    "Error budget remaining per workload",
    ["workload_id"],
    registry=_registry,
)
_burn_rate_g = Gauge(
    "platform_slo_burn_rate",
    "Burn rate per workload (1.0 = sustainable)",
    ["workload_id"],
    registry=_registry,
)


@router.get("/metrics")
def metrics() -> Response:
    for w in get_slo_store().list():
        s = w.state()
        _budget_remaining.labels(workload_id=w.workload_id).set(error_budget_remaining(w.slo, s))
        _burn_rate_g.labels(workload_id=w.workload_id).set(burn_rate(w.slo, s))
    return Response(generate_latest(_registry), media_type=CONTENT_TYPE_LATEST)
