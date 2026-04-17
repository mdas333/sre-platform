"""Tests for SLO math. Pure functions, no I/O, no Kubernetes."""

from __future__ import annotations

import math

import pytest

from slo.model import (
    SLO,
    SLOState,
    burn_rate,
    error_budget_remaining,
    error_budget_total,
    health_state,
)

DAY = 86400


@pytest.fixture
def slo_999() -> SLO:
    """99.9% over 7 days on http_success_rate — a common web-service target."""
    return SLO(target=99.9, window_seconds=7 * DAY, indicator="http_success_rate")


def test_slo_validates_target_range():
    with pytest.raises(ValueError):
        SLO(target=0, window_seconds=DAY, indicator="x")
    with pytest.raises(ValueError):
        SLO(target=100.1, window_seconds=DAY, indicator="x")
    with pytest.raises(ValueError):
        SLO(target=99.9, window_seconds=0, indicator="x")


def test_slo_state_rejects_negatives():
    with pytest.raises(ValueError):
        SLOState(total_events=-1, failed_events=0, elapsed_seconds=0)
    with pytest.raises(ValueError):
        SLOState(total_events=10, failed_events=20, elapsed_seconds=0)


def test_error_budget_total_scales_linearly(slo_999: SLO):
    s = SLOState(total_events=10_000, failed_events=0, elapsed_seconds=DAY)
    # 0.1% of 10,000 = 10 permitted failures
    assert error_budget_total(slo_999, s) == pytest.approx(10.0)


def test_error_budget_remaining_tracks_failures(slo_999: SLO):
    s = SLOState(total_events=10_000, failed_events=3, elapsed_seconds=DAY)
    assert error_budget_remaining(slo_999, s) == pytest.approx(7.0)


def test_error_budget_remaining_goes_negative_on_breach(slo_999: SLO):
    s = SLOState(total_events=10_000, failed_events=15, elapsed_seconds=DAY)
    assert error_budget_remaining(slo_999, s) == pytest.approx(-5.0)


def test_burn_rate_zero_when_no_failures(slo_999: SLO):
    s = SLOState(total_events=10_000, failed_events=0, elapsed_seconds=DAY)
    assert burn_rate(slo_999, s) == 0.0


def test_burn_rate_exactly_one_at_sustainable_pace(slo_999: SLO):
    # sustainable: consume 10 failures over 7 days at a constant rate.
    # At day 1, that's 10 * 1/7 = ~1.428 permitted failures.
    s = SLOState(total_events=10_000, failed_events=2, elapsed_seconds=DAY)
    # failures_per_sec = 2/86400
    # sustainable_per_sec = 10/(7*86400)
    # burn_rate = (2/86400) / (10/604800) = 2 * 7 / 10 = 1.4
    assert burn_rate(slo_999, s) == pytest.approx(1.4)


def test_burn_rate_infinite_when_no_budget_but_failures():
    slo = SLO(target=100.0, window_seconds=DAY, indicator="x")
    s = SLOState(total_events=1000, failed_events=1, elapsed_seconds=10)
    assert math.isinf(burn_rate(slo, s))


def test_health_healthy_when_fresh(slo_999: SLO):
    s = SLOState(total_events=10_000, failed_events=1, elapsed_seconds=DAY)
    assert health_state(slo_999, s) == "healthy"


def test_health_burning_at_high_rate(slo_999: SLO):
    # Consuming budget 3x faster than sustainable.
    s = SLOState(total_events=10_000, failed_events=4, elapsed_seconds=DAY)
    # burn_rate = (4/86400) / (10/604800) = 2.8
    assert health_state(slo_999, s) == "burning"


def test_health_breached_when_budget_exhausted(slo_999: SLO):
    s = SLOState(total_events=10_000, failed_events=11, elapsed_seconds=DAY)
    assert health_state(slo_999, s) == "breached"


def test_health_healthy_with_no_events(slo_999: SLO):
    # No traffic yet: cannot be burning, cannot be breached.
    s = SLOState(total_events=0, failed_events=0, elapsed_seconds=0)
    assert health_state(slo_999, s) == "healthy"


def test_health_threshold_configurable(slo_999: SLO):
    s = SLOState(total_events=10_000, failed_events=2, elapsed_seconds=DAY)  # burn=1.4
    # default threshold 2.0 — healthy
    assert health_state(slo_999, s) == "healthy"
    # tighter threshold 1.0 — now classified as burning
    assert health_state(slo_999, s, burn_threshold=1.0) == "burning"
