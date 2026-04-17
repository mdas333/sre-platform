"""
SLO math — the reliability signal.

All functions are pure and deterministic so they can be unit-tested
without Kubernetes or Vault. The Platform API's `/health` and `/slo`
endpoints call into here with counters aggregated from cluster telemetry.

See shared/adr/0010-slo-math-over-dashboards.md for the rationale.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import inf
from typing import Literal

HealthState = Literal["healthy", "burning", "breached"]


@dataclass(frozen=True, slots=True)
class SLO:
    """Declarative SLO target registered at workload creation."""

    target: float  # e.g. 99.9 meaning 99.9% success rate
    window_seconds: int  # rolling window, e.g. 7 * 86400
    indicator: str  # e.g. "http_success_rate"

    def __post_init__(self) -> None:
        if not 0 < self.target <= 100:
            raise ValueError(f"SLO target must be in (0, 100]; got {self.target}")
        if self.window_seconds <= 0:
            raise ValueError(f"SLO window must be > 0; got {self.window_seconds}")


@dataclass(frozen=True, slots=True)
class SLOState:
    """Observed state inside the SLO window."""

    total_events: int
    failed_events: int
    elapsed_seconds: int

    def __post_init__(self) -> None:
        if self.total_events < 0 or self.failed_events < 0 or self.elapsed_seconds < 0:
            raise ValueError("SLOState counters must be non-negative")
        if self.failed_events > self.total_events:
            raise ValueError("failed_events cannot exceed total_events")


def error_budget_total(slo: SLO, state: SLOState) -> float:
    """Total permitted failures in the window given observed volume."""
    return (1 - slo.target / 100.0) * state.total_events


def error_budget_remaining(slo: SLO, state: SLOState) -> float:
    """Remaining budget, can be negative when breached."""
    return error_budget_total(slo, state) - state.failed_events


def burn_rate(slo: SLO, state: SLOState) -> float:
    """
    Burn rate = (consumed per second) / (sustainable per second).

    Sustainable means exhausting exactly 100% of budget by the end of the
    window. burn_rate >= 1 means consumption trend breaches by the end,
    < 1 means you finish with budget to spare. inf when no budget exists
    but failures have occurred.
    """
    if state.total_events == 0 or state.elapsed_seconds == 0:
        return 0.0
    total_budget = error_budget_total(slo, state)
    if total_budget == 0:
        return inf if state.failed_events > 0 else 0.0
    consumed_per_second = state.failed_events / state.elapsed_seconds
    sustainable_per_second = total_budget / slo.window_seconds
    return consumed_per_second / sustainable_per_second


def health_state(slo: SLO, state: SLOState, burn_threshold: float = 2.0) -> HealthState:
    """
    Classify a workload's current position relative to its SLO.

    - `breached`: budget is exhausted (or overdrawn).
    - `burning`:  budget remains, but burn_rate >= threshold (default 2x).
    - `healthy`:  otherwise.
    """
    if error_budget_remaining(slo, state) <= 0 and state.total_events > 0:
        return "breached"
    if burn_rate(slo, state) >= burn_threshold:
        return "burning"
    return "healthy"
