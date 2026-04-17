"""Tests for SLOStore — registry + counter validation invariants."""

from __future__ import annotations

import pytest

from slo.model import SLO
from slo.store import SLOStore


@pytest.fixture
def slo_target() -> SLO:
    return SLO(target=99.9, window_seconds=86400, indicator="http_success_rate")


def test_register_returns_entry_with_zero_counters(slo_target: SLO):
    store = SLOStore()
    entry = store.register("demo-app", slo_target)
    assert entry.workload_id == "demo-app"
    assert entry.total_events == 0
    assert entry.failed_events == 0


def test_record_accumulates_counters(slo_target: SLO):
    store = SLOStore()
    store.register("demo-app", slo_target)
    store.record("demo-app", total=100, failed=2)
    store.record("demo-app", total=50, failed=1)
    entry = store.get("demo-app")
    assert entry is not None
    assert entry.total_events == 150
    assert entry.failed_events == 3


def test_record_rejects_negative_deltas(slo_target: SLO):
    store = SLOStore()
    store.register("demo-app", slo_target)
    with pytest.raises(ValueError, match="non-negative"):
        store.record("demo-app", total=-1, failed=0)
    with pytest.raises(ValueError, match="non-negative"):
        store.record("demo-app", total=10, failed=-1)


def test_record_rejects_failed_exceeding_total(slo_target: SLO):
    store = SLOStore()
    store.register("demo-app", slo_target)
    with pytest.raises(ValueError, match="failed events cannot exceed total"):
        store.record("demo-app", total=10, failed=20)


def test_record_returns_none_for_unknown_workload():
    store = SLOStore()
    assert store.record("missing", total=1, failed=0) is None


def test_register_is_thread_safe_like(slo_target: SLO):
    """Two back-to-back registrations of the same id overwrite cleanly."""
    store = SLOStore()
    e1 = store.register("same-id", slo_target)
    e2 = store.register("same-id", slo_target)
    assert e1 is not e2
    assert store.get("same-id") is e2
