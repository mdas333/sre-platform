# Project 01 — sre-platform

[![ci](https://github.com/mdas333/sre-platform/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/mdas333/sre-platform/actions/workflows/ci.yml)

An internal developer platform on Kubernetes, with SRE-grade reliability engineering built in — not bolted on.

Operating Kubernetes reliably is more than deployment scripts: it requires observable, self-healing infrastructure with meaningful health signals. This project implements a working platform that covers the full loop — declarative cluster lifecycle, a developer-facing Platform API, error-budget-aware health, HMAC-signed audit receipts, OpenTelemetry-native observability, event-driven autoscaling on a separate demo workload (the Platform API itself runs always-on), GitOps deployment, and images signed in CI with keyless cosign via GitHub OIDC.

The Platform API exposes only a demo-grade surface in P1: no auth middleware, no quota enforcement, no admission-policy hooks. Those guardrails are on the Project 03 roadmap (`paved-road`), which revisits every component in a multi-environment form.

## What it does

The project stands up a four-node k3d cluster and a Platform API that lets you:

- **Create a workload** with a declared SLO target (`POST /workloads`).
- **Query workload health** as an error-budget state (`GET /workloads/{id}/health`).
- **Scale a workload** with an auditable signed receipt (`POST /workloads/{id}/scale`).
- **Read the SLO math** — error budget remaining, burn rate (`GET /workloads/{id}/slo`).
- **Get a plain-English status** via an LLM adapter, disabled by default (`GET /workloads/{id}/explain`).
- **See a 0–100 cluster health score** (`GET /cluster/health`).
- **Audit every mutating operation** via a signed receipt stream (`GET /audit`).

The four primitive requirements — build a cluster, scale it, health-check it, monitor it — all surface as implementation details behind this API.

## Architecture

```
                           ┌───────────────────────────────────────┐
                           │           k3d cluster                 │
                           │  1 server + 3 agents (Docker-backed)  │
                           └───────────────────────────────────────┘
                                          │
      ┌───────────────────────────────────┼───────────────────────────────────┐
      │                                   │                                   │
┌─────▼──────┐   ┌───────────────┐   ┌────▼─────┐   ┌──────────┐   ┌─────────▼────────┐
│  ArgoCD    │   │ Vault (dev)   │   │ KEDA HTTP│   │ cosign   │   │ OTel Collector   │
│ (GitOps)   │   │ K8s-auth role │   │ scaling  │   │ (signing)│   │ k8s + kubelet +  │
└─────┬──────┘   └───────────┬───┘   └────┬─────┘   └──────────┘   │ hostmetrics +   │
      │                      │            │                         │ filelog + OTLP  │
      │ reconciles           │            │ scales 0..5             └────────┬─────────┘
      ▼                      ▼            ▼                                   │ OTLP
┌─────────────────────────────────────────────────────────────┐               │
│                    Platform API (FastAPI)                   │               │
│  /workloads  /cluster/*  /audit  /explain  /metrics         │───────────────┤
│                                                             │               │
│  SLO math │ HMAC receipts │ k8s client │ Vault client │ LLM │               │
└─────────────────────────────────────────────────────────────┘               │
                                                                              ▼
                                                                    ┌───────────────────┐
                                                                    │      SigNoz       │
                                                                    │ (ClickHouse-backed│
                                                                    │  metrics, logs,   │
                                                                    │  traces — unified)│
                                                                    └───────────────────┘
```

(A higher-fidelity diagram lives at `docs/architecture.png`.)

## Quick start

Prerequisites: Docker Desktop running, Homebrew available.

```bash
../shared/scripts/preflight.sh     # verify toolchain
./scripts/cluster-up.sh            # ~8 min: cluster + vault + argocd + signoz + keda + api
./scripts/demo.sh                  # narrated walkthrough
```

Teardown: `./scripts/cluster-down.sh`.

## The Platform API

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/workloads` | Create workload from spec (name, image, replicas, SLO target) |
| GET | `/workloads` | List all platform-managed workloads |
| GET | `/workloads/{id}` | Workload detail |
| GET | `/workloads/{id}/health` | Error-budget-aware state (`healthy` / `burning` / `breached`) |
| GET | `/workloads/{id}/slo` | SLO target, error budget, burn rate |
| POST | `/workloads/{id}/scale` | Scale replicas; emits a signed receipt |
| GET | `/workloads/{id}/events` | Recent warning events for the workload |
| GET | `/workloads/{id}/explain` | LLM-generated plain-English status (feature-gated) |
| GET | `/cluster/health` | Aggregate 0–100 cluster health score |
| GET | `/cluster/nodes` | Node status, capacity, conditions |
| GET | `/audit` | Signed operation log (verifiable offline) |
| GET | `/metrics` | Prometheus scrape endpoint |
| GET | `/healthz`, `/readyz` | Kubernetes probes |

OpenAPI docs at `/docs` when running.

## SLO math (the reliability signal)

Each workload registers an SLO at creation time — a target, a rolling window, and an indicator. The Platform API computes:

- `error_budget_total = (1 − target) × total_events_in_window`
- `error_budget_consumed = failures_in_window`
- `error_budget_remaining = total − consumed`
- `burn_rate` — consumed rate relative to sustainable rate

`/health` returns `healthy`, `burning`, or `breached` based on budget position — not just HTTP 200. The full math is at `/slo` and as the Prometheus gauges `platform_slo_error_budget_remaining` and `platform_slo_burn_rate`.

**Telemetry source (P1 demo):** the Platform API self-instruments its own request counters (`platform_http_requests_total`, `platform_http_failures_total`) and exposes them on `/metrics`. The OpenTelemetry Collector scrapes the endpoint and forwards to SigNoz — this is standard Prometheus white-box instrumentation. `scripts/load.sh` injects real HTTP traffic with a configurable failure rate so the error budget visibly burns down. The in-memory SLO counters are bounded and reset on pod restart; a production deployment would ingest ingress / service-mesh metrics over rolling 7- or 30-day windows and persist them.

See [ADR 0010](../shared/adr/0010-slo-math-over-dashboards.md) for the decision rationale.

## Signed receipts (the audit differentiator)

Every mutating operation emits a receipt signed with HMAC-SHA256 using a key rotated daily from Vault:

```json
{
  "op_id": "01J2HR5...",
  "ts": "2026-04-16T18:22:11Z",
  "actor": "platform-api@sre-platform",
  "action": "scale",
  "workload_id": "demo-app",
  "before": { "replicas": 2 },
  "after":  { "replicas": 5 },
  "trace_id": "4bf92f35...",
  "kid": "key-2026-04-16",
  "hmac": "mQ9vL8..."
}
```

`/audit` returns the stream. `scripts/verify-receipt < receipt.json` validates offline. See [ADR 0009](../shared/adr/0009-hmac-vault-for-receipts.md).

## Scaling

Two layers, both demonstrated.

**Cluster-level** (`scripts/scale-cluster-up.sh`, `scripts/scale-cluster-down.sh`):

```bash
# Add an agent node
k3d node create extra --cluster sre-platform --role agent

# Drain and remove
kubectl drain k3d-extra-0 --ignore-daemonsets --delete-emptydir-data
k3d node delete k3d-extra-0
```

![cluster-level scale](./docs/demos/cluster-scale.gif)

**Workload-level** (KEDA on `demo-app`). The Platform API itself is the control plane and runs always-on (`minReplicas: 2`) — scaling the API to zero would make `/workloads`, `/audit`, and `/health` unreachable on cold start. The scale-to-zero narrative therefore targets a *separate* `demo-app` workload (`k8s/demo-app/keda-scaledobject.yaml`): `minReplicaCount: 0`, `maxReplicaCount: 3`, triggered by a cron window.

The demo recording below captures the full cycle — patch the ScaledObject's cron window to the current minute, KEDA polls every 15 s and scales `demo-app` from 0 to 2 replicas Ready in ~18 s, then the window is restored and the cooldown timer returns the workload to zero.

![keda scale-to-zero](./docs/demos/keda-scale.gif)

The cron trigger is deliberate for a reproducible demo; production workloads would use HTTP-rate, Prometheus, Kafka, or SQS triggers depending on their signal source. See [ADR 0005](../shared/adr/0005-keda-over-hpa.md).

## Observability (SigNoz, OpenTelemetry-native)

The OpenTelemetry Collector runs as a daemonset + deployment with five receivers:

- `k8s_cluster` — pod, deployment, node state.
- `kubeletstats` — per-pod CPU and memory.
- `hostmetrics` — node CPU, memory, disk.
- `otlp` (gRPC) — from the Platform API.
- `filelog` — container logs.

All signals flow over OTLP to SigNoz. Metrics, logs, and traces sit in one ClickHouse datastore, so a metric spike is click-through to the trace and log line that caused it. See [ADR 0004](../shared/adr/0004-signoz-over-prometheus-grafana.md).

## Design decisions

| # | Decision |
|---|----------|
| [0001](../shared/adr/0001-monorepo.md) | Monorepo for the portfolio arc |
| [0002](../shared/adr/0002-k3d-over-kind.md) | k3d for local Kubernetes |
| [0003](../shared/adr/0003-opentofu-over-terraform.md) | OpenTofu over Terraform |
| [0004](../shared/adr/0004-signoz-over-prometheus-grafana.md) | SigNoz for observability |
| [0005](../shared/adr/0005-keda-over-hpa.md) | KEDA for workload autoscaling |
| [0006](../shared/adr/0006-vault-k8s-auth.md) | Vault Kubernetes auth for secrets |
| [0007](../shared/adr/0007-fastapi-with-official-k8s-client.md) | FastAPI and the official k8s client |
| [0008](../shared/adr/0008-sigstore-cosign-for-images.md) | Sigstore cosign for image signing |
| [0009](../shared/adr/0009-hmac-vault-for-receipts.md) | HMAC with Vault for operation receipts |
| [0010](../shared/adr/0010-slo-math-over-dashboards.md) | SLO math in the Platform API |
| [0011](../shared/adr/0011-pluggable-llm-backend.md) | Pluggable LLM backend |

## Tests

```bash
cd platform-api
uv sync
uv run pytest -v
uv run ruff check src tests
```

Suites in `platform-api/tests/`:

- `test_slo_math.py` — budget math, rolling windows, edge cases (zero events, zero budget, target = 100), configurable burn thresholds.
- `test_slo_store.py` — registry invariants: record() rejects negative deltas and `failed > total`.
- `test_receipts.py` — HMAC signing and verifier round-trip, key rotation, canonical JSON determinism, constant-time comparison, tampering detection.

## CI and signed images

On every push to `main`, the GitHub Actions workflow (`.github/workflows/ci.yml`) runs three jobs:

1. **Platform API — ruff + pytest.** uv sync, ruff check, pytest.
2. **Kubernetes manifests — kubeconform.** Strict schema validation of `k8s/**` using the Datree CRD catalog so KEDA ScaledObject and similar CRDs are recognised.
3. **Build, sign, push to GHCR.** Docker buildx with GHA cache, metadata-driven tags (`main`, `main-<sha>`, `latest`), push to `ghcr.io/mdas333/sre-platform/platform-api`, then **keyless Sigstore cosign** — the workflow's OIDC identity is the only signer; no private key is generated or stored. Verification chains the signature back to `refs/heads/main` of this repo.

Verify any published image locally:

```bash
scripts/verify-image.sh ghcr.io/mdas333/sre-platform/platform-api:main
# Runs:
# cosign verify \
#   --certificate-identity-regexp '.*mdas333/sre-platform.*' \
#   --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
#   ghcr.io/mdas333/sre-platform/platform-api:main
```

ArgoCD in the cluster reconciles the `k8s/` tree on `main`, so merging a commit that bumps an image tag (or any manifest) triggers a rollout.

## Status

- [x] Workspace skeleton, 11 ADRs, capabilities index.
- [x] OpenTofu cluster definition (`kreuzwerker/k3d`-style `null_resource` with idempotent create / destroy); scale-up / scale-down scripts verified live (4 ↔ 5 nodes).
- [x] Vault, ArgoCD, SigNoz, KEDA, OTel Collector install scripts — chained in `cluster-up.sh`; Vault Kubernetes auth bootstrapped idempotently.
- [x] Platform API: 17 routes, 31 unit tests passing, ruff clean, end-to-end smoke against the live cluster (real node list, signed receipt with Vault-sourced `kid`, Prometheus metrics).
- [x] Container image (Dockerfile multi-stage, non-root, read-only rootfs); GHCR push and keyless cosign signing in CI; image verified offline with `scripts/verify-image.sh`.
- [x] ArgoCD Application — `sre-platform` — syncs 12 resources from `main` (Synced/Healthy).
- [x] Scaling demo recordings — cluster-level and KEDA scale-from-zero, under `docs/demos/`.
