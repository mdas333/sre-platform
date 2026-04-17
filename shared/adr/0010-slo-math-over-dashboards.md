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

The full math is exposed at `/workloads/{id}/slo` and as the Prometheus metric `platform_slo_error_budget_remaining_seconds` per workload.

## Consequences

**Upside**

- Moves the health model from "is it up" to "is it meeting its contract".
- The Prometheus metric can drive alerting: alert on burning, not on CPU.
- Error-budget thinking is the single most common request in senior-SRE interview loops.

**Downside**

- Requires a source of request success/failure counts per workload. Project 01 relies on the OpenTelemetry Collector's metrics pipeline; workloads not instrumented with OTel will show zero events and an N/A budget. Documented in `docs/slo-model.md`.
