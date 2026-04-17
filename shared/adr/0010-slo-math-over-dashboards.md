# ADR 0010 — SLO math in the Platform API, not just dashboards

Status: Accepted
Date: 2026-04-16

## Context

Many portfolio projects stop at "here is a Grafana dashboard with uptime". That is not reliability engineering; it is dashboard engineering. The real signal for a senior SRE interview is: does the candidate think in terms of error budgets and burn rates?

A health endpoint that returns HTTP 200 whenever the pod is alive has almost no operational value. A health endpoint that returns `burning` when the workload is consuming its error budget too fast is a very different signal.

## Decision

Each workload created through the Platform API registers an SLO at creation time:

- `target` (e.g. 99.9)
- `window` (rolling duration, e.g. `7d`)
- `indicator` (e.g. `http_success_rate`)

The Platform API computes, per workload:

- `error_budget_total = (1 − target) × total_events_in_window`
- `error_budget_consumed = failures_in_window`
- `error_budget_remaining = total − consumed`
- `burn_rate` (consumed rate divided by the sustainable budget rate)

The `/health` endpoint returns one of three states:

- `healthy` — budget > 50% remaining.
- `burning` — budget burning significantly faster than sustainable.
- `breached` — budget exhausted.

The full math is exposed at `/workloads/{id}/slo` and as the Prometheus gauges `platform_slo_error_budget_remaining` and `platform_slo_burn_rate` per workload (labelled by `workload_id`).

## Telemetry contract

The math is signal-source-agnostic — it accepts total and failed event counters and returns budget state. P1 and a production deployment differ only in where those counters come from:

- **P1 demo mode.** The Platform API self-instruments its own request rate via `SLOStore.record(total=..., failed=...)` fed from a small HTTP middleware counter. `scripts/load.sh` drives real traffic with a configurable failure rate (default 2%). The counters live in-memory and reset on pod restart; this is a deliberate P1 limitation, documented here and in the README. The window is evaluated from the per-workload `created_at` timestamp, clamped to the configured SLO window length.
- **Production mode (P3).** Counters are ingested from ingress/service-mesh metrics (e.g. Traefik or Envoy) queried via SigNoz over a true rolling 7- or 30-day window; the Platform API becomes a compute and API surface on top of persistent signal storage. Persistence and survival-of-restart are the key differences; the math module itself is unchanged.

The trade-off is made explicit so a reviewer reading the code sees "in-memory is a scoped P1 choice, not a design gap."

## Consequences

**Upside**

- Moves the health model from "is it up" to "is it meeting its contract".
- The Prometheus gauges can drive alerting: alert on burning, not on CPU.
- The math module has a narrow interface (two counters + a SLO) and is therefore unit-testable without any infrastructure — the test suite covers edge cases like zero events, zero budget, burn rate → ∞, and budget-exhausted.

**Downside**

- In-memory counters reset on pod restart in P1. A reviewer who wants to see persistent windowed SLOs should look at P3.
- Workloads that are not instrumented (e.g. deployed outside the Platform API) show zero events and an N/A budget. This is honest: the platform can only judge what it can observe.
