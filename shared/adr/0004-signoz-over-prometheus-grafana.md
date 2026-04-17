# ADR 0004 — SigNoz for observability (in place of Prometheus + Grafana + Loki + Tempo)

Status: Accepted
Date: 2026-04-16

## Context

The project needs unified observability across metrics, logs, and traces. The default stack in 2019–2022 was Prometheus (metrics) + Grafana (visualisation) + Loki (logs) + Tempo (traces). That is four separate backends, four retention policies, and a cross-tool correlation story that relies on shared labels.

OpenTelemetry has become the vendor-neutral telemetry standard. Backends that are OTel-native from the ground up — rather than retrofitting OTel compatibility — offer a cleaner correlation story.

## Decision

Use SigNoz: an OpenTelemetry-native, open-source observability platform backed by ClickHouse. Deployed on the k3d cluster via its official Helm chart.

## Consequences

**Upside**

- Single backend for metrics, logs, and traces. Correlation is a click, not a label lookup across tools.
- OpenTelemetry-first. The OpenTelemetry Collector is the only ingestion path and is configured explicitly in the repo.
- MIT licensed; self-hostable; free to run forever.
- ClickHouse-backed means query performance is good even on a laptop.

**Downside**

- Smaller community than the Grafana stack. Documentation is decent; blog-post ecosystem is thinner.
- Not a drop-in replacement for existing Grafana dashboards. Dashboard JSON is SigNoz-specific.

## Alternatives considered

- **Prometheus + Grafana + Loki + Tempo** — rejected; the story is four tools, not one. The correlation argument is the whole point of choosing observability stack in 2026.
- **Datadog / New Relic / Honeycomb** — rejected; paid SaaS violates the zero-cost constraint.
- **Elastic Observability** — rejected; heavier to run on a laptop.
