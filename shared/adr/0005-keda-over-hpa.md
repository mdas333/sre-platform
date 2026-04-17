# ADR 0005 — KEDA for workload autoscaling

Status: Accepted
Date: 2026-04-16

## Context

The scaling story for Project 01 requires demonstrating pod-level autoscaling that goes beyond CPU and memory. Two specific capabilities matter:

1. Scale from zero under load (not just "scale up to an ever-larger floor").
2. Scale on request rate (or any external signal), not only resource utilisation.

The in-tree `HorizontalPodAutoscaler` can do CPU and memory scaling, and custom metrics via a metrics adapter — but it does not natively support scale-to-zero on HTTP, and the custom-metrics plumbing is fiddly.

## Decision

Use KEDA (Kubernetes Event-Driven Autoscaling) with the HTTP add-on. A `ScaledObject` targets the Platform API Deployment:

- `minReplicas: 0`
- `maxReplicas: 5`
- `cooldownPeriod: 120s`
- Scaling signal: incoming HTTP request rate.

## Consequences

**Upside**

- Scale-to-zero is one line of YAML — the headline capability.
- KEDA supports a broad set of scalers (Kafka, SQS, Prometheus, cron, GCP PubSub, etc.) which carries over to future projects.
- Cleaner operational pattern than wiring up the Prometheus adapter for HPA.

**Downside**

- Another component to install and understand. The HTTP add-on in particular is newer than core KEDA; documentation is still evolving.
- A classic HPA fallback is kept in `k8s/platform-api/hpa.yaml.disabled`; swapping to it is a one-line change.
