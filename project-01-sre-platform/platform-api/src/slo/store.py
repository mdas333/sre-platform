"""
In-memory SLO registry.

Workloads register their SLO target at creation time; subsequent reads
pull back the definition plus observed state. State counters would be
sourced from the OTel Collector's metrics in a full implementation; in
Project 01 the store exposes hooks that can be driven either by a
metrics pull or by direct test fixtures.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

from .model import SLO, SLOState


@dataclass
class WorkloadSLO:
    workload_id: str
    slo: SLO
    created_at: float = field(default_factory=time.time)

    total_events: int = 0
    failed_events: int = 0

    def state(self) -> SLOState:
        elapsed = min(int(time.time() - self.created_at), self.slo.window_seconds)
        return SLOState(
            total_events=self.total_events,
            failed_events=self.failed_events,
            elapsed_seconds=elapsed,
        )


class SLOStore:
    """Thread-safe in-memory registry of workload SLOs."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._store: dict[str, WorkloadSLO] = {}

    def register(self, workload_id: str, slo: SLO) -> WorkloadSLO:
        with self._lock:
            entry = WorkloadSLO(workload_id=workload_id, slo=slo)
            self._store[workload_id] = entry
            return entry

    def get(self, workload_id: str) -> WorkloadSLO | None:
        with self._lock:
            return self._store.get(workload_id)

    def list(self) -> list[WorkloadSLO]:
        with self._lock:
            return list(self._store.values())

    def record(self, workload_id: str, *, total: int, failed: int) -> WorkloadSLO | None:
        with self._lock:
            entry = self._store.get(workload_id)
            if entry is None:
                return None
            entry.total_events += total
            entry.failed_events += failed
            return entry
