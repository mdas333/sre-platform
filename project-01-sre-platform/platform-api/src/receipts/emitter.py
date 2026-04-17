"""
Receipt emitter — appends to an in-memory store and emits as an OTel log.

The in-memory store backs the `/audit` endpoint for quick demos. In a
larger deployment the OTel log pipeline would persist receipts to SigNoz
(ClickHouse) and `/audit` would query that; the in-memory fallback stays
useful when SigNoz is unavailable.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from collections import deque
from typing import Any

from .signer import sign

logger = logging.getLogger(__name__)


class ReceiptEmitter:
    """Signs receipts on the way out and stores the last N in memory."""

    def __init__(self, key_provider, actor: str = "platform-api@sre-platform", max_retained: int = 200):
        self._key_provider = key_provider  # returns (kid, key_bytes)
        self._actor = actor
        self._buffer: deque[dict[str, Any]] = deque(maxlen=max_retained)
        self._lock = threading.RLock()

    def emit(self, *, action: str, workload_id: str, before: dict | None, after: dict | None,
             trace_id: str | None = None) -> dict[str, Any]:
        kid, key = self._key_provider()
        raw = {
            "op_id": str(uuid.uuid4()),
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "actor": self._actor,
            "action": action,
            "workload_id": workload_id,
            "before": before or {},
            "after": after or {},
            "trace_id": trace_id,
            "kid": kid,
        }
        signed = sign(raw, key)
        with self._lock:
            self._buffer.append(signed)
        logger.info("receipt emitted", extra={"receipt_op_id": signed["op_id"], "action": action})
        return signed

    def recent(self, n: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._buffer)[-n:]
