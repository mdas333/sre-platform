# Project 01 — sre-platform

An internal developer platform on Kubernetes, with SRE-grade reliability engineering built in — not bolted on.

Operating Kubernetes reliably is more than deployment scripts: it requires observable, self-healing infrastructure with meaningful health signals. This project implements a working platform that covers the full loop — declarative cluster lifecycle, a developer-facing Platform API, error-budget-aware health, cryptographically signed audit receipts, OpenTelemetry-native observability, event-driven autoscaling with scale-to-zero, GitOps deployment, and signed container images.

## What it does

The project stands up a four-node k3d cluster and a Platform API that lets you:

- **Create a workload** with a declared SLO target (`POST /workloads`).
- **Query workload health** as an error-budget state (`GET /workloads/{id}/health`).
- **Scale a workload** with an auditable signed receipt (`POST /workloads/{id}/scale`).
- **Read the SLO math** — error budget remaining, burn rate (`GET /workloads/{id}/slo`).
- **Get a plain-English status** via an LLM adapter (`GET /workloads/{id}/explain`).
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

`/health` returns `healthy`, `burning`, or `breached` based on budget position — not just HTTP 200. The full math is at `/slo` and as the Prometheus metric `platform_slo_error_budget_remaining_seconds`.

See `docs/slo-model.md` for the formulas and worked examples, and [ADR 0010](../shared/adr/0010-slo-math-over-dashboards.md) for the decision rationale.

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
k3d node create extra-agent --cluster sre-platform --role agent

# Drain and remove
kubectl drain k3d-sre-platform-agent-2 --ignore-daemonsets --delete-emptydir-data
k3d node delete k3d-sre-platform-agent-2
```

**Workload-level** (KEDA HTTP add-on). A `ScaledObject` targets the Platform API Deployment with `minReplicas=0`, `maxReplicas=5`, `cooldownPeriod=120s`, scaling on request rate.

Demonstration: `scripts/load.sh` generates load with `hey`; `kubectl get pods -w` shows scale 0→N and back to 0. Recording lives at `docs/scaling-demo.md`. See [ADR 0005](../shared/adr/0005-keda-over-hpa.md).

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

Suites:

- `test_slo_math.py` — budget math, rolling windows, edge cases (zero events, zero budget, target = 100).
- `test_receipts.py` — HMAC signing and verifier round-trip, key rotation, canonical JSON determinism.
- `test_health_score.py` — the aggregate 0–100 computation.
- `test_platform_api_e2e.py` — the full route surface against a fake Kubernetes client.

## CI

On push to `main`, GitHub Actions runs: ruff lint → pytest → Docker image build → cosign sign → push to GHCR. ArgoCD in the cluster detects the new tag and syncs.

Workflow file: `.github/workflows/ci.yml`.

## Status

- [x] Workspace skeleton and governance.
- [x] Architecture decision records (11) and glossary.
- [ ] OpenTofu cluster definition.
- [ ] Vault, ArgoCD, SigNoz, KEDA, OTel Collector install scripts.
- [ ] Platform API (FastAPI scaffold, SLO, receipts, LLM adapter).
- [ ] Image signing and CI pipeline.
- [ ] Scaling demo recordings.
- [ ] Architecture diagram.
