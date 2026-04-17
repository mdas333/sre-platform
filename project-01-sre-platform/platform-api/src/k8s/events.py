"""Event queries — warning-level events across the platform namespace."""

from __future__ import annotations

import logging

from .client import core_v1, ensure_loaded

logger = logging.getLogger(__name__)


def recent_warnings(namespace: str, limit: int = 20) -> list[dict]:
    if not ensure_loaded():
        return []
    try:
        events = core_v1().list_namespaced_event(
            namespace=namespace,
            field_selector="type=Warning",
            limit=limit,
        )
    except Exception:
        logger.exception("failed to read events in %s", namespace)
        return []
    return [
        {
            "reason": e.reason,
            "message": e.message,
            "involved": f"{e.involved_object.kind}/{e.involved_object.name}",
            "count": e.count,
            "last_seen": e.last_timestamp.isoformat() if e.last_timestamp else None,
        }
        for e in events.items
    ]
