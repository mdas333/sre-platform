"""
/workloads/{id}/explain — LLM-generated plain-English status.

Gated off by default. When enabled and a backend is available, the
endpoint builds a structured prompt from workload state and returns a
short narrative. When disabled or the backend fails, the endpoint
returns structured-only data with `narrative: null` at HTTP 200 (graceful).
"""

from __future__ import annotations

import logging
import threading

from fastapi import APIRouter, HTTPException

from config import get_settings
from llm.backend import make_backend

from .state import get_slo_store

logger = logging.getLogger(__name__)

router = APIRouter()

_backend = None
_backend_attempted = False
_backend_lock = threading.Lock()


def _backend_singleton():
    global _backend, _backend_attempted
    with _backend_lock:
        if not _backend_attempted:
            _backend = make_backend()
            _backend_attempted = True
        return _backend


def _build_prompt(workload_id: str, slo_view: dict) -> str:
    return (
        "You are an SRE assistant. In 2-3 sentences, summarise this workload's "
        "reliability state for a developer who just checked on it. Be concrete; "
        "reference the numbers. Do not speculate about causes.\n\n"
        f"Workload: {workload_id}\n"
        f"SLO target: {slo_view['target']}% ({slo_view['indicator']})\n"
        f"Window: {slo_view['window_seconds']}s\n"
        f"Events observed: {slo_view['total_events']} total, {slo_view['failed_events']} failed\n"
        f"Error budget remaining: {slo_view['error_budget_remaining']}\n"
        f"Burn rate: {slo_view['burn_rate']}x sustainable\n"
        f"State: {slo_view['state']}\n"
    )


@router.get("/workloads/{workload_id}/explain")
def workload_explain(workload_id: str) -> dict:
    store = get_slo_store()
    entry = store.get(workload_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="workload not found")

    from .workloads import _slo_view  # local import to avoid circular

    slo_view = _slo_view(store, workload_id)

    settings = get_settings()
    if not settings.enable_llm_explain:
        return {"workload_id": workload_id, "slo": slo_view, "narrative": None, "reason": "disabled"}

    backend = _backend_singleton()
    if backend is None:
        return {"workload_id": workload_id, "slo": slo_view, "narrative": None, "reason": "backend_unavailable"}

    try:
        narrative = backend.generate(_build_prompt(workload_id, slo_view))
    except Exception:
        logger.exception("LLM generation failed; degrading")
        return {"workload_id": workload_id, "slo": slo_view, "narrative": None, "reason": "generate_failed"}

    return {"workload_id": workload_id, "slo": slo_view, "narrative": narrative, "backend": backend.name}
