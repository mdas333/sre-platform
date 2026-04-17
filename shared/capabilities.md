# Capabilities

What this repository implements, with a pointer to the backing code and ADR
for each capability. A reader's index, not a summary — use it to navigate.

## Cluster lifecycle

Kubernetes cluster lifecycle is managed declaratively with OpenTofu and the
`kreuzwerker/k3d` provider. The cluster has one server and three agents;
`scripts/cluster-up.sh` and `scripts/cluster-down.sh` provide idempotent
bring-up and teardown from a single command.

- Implementation: `project-01-sre-platform/infrastructure/cluster/`
- Design: [ADR 0002](./adr/0002-k3d-over-kind.md),
  [ADR 0003](./adr/0003-opentofu-over-terraform.md).

## Two layers of scaling

- Cluster-level: `scripts/scale-cluster-up.sh` adds an agent node;
  `scripts/scale-cluster-down.sh` cordons, drains, and removes one.
- Workload-level: KEDA drives a demo workload from zero under load and back
  to zero after idle. The Platform API itself runs always-on — scaling the
  control plane to zero would make the API unreachable.

- Implementation: `project-01-sre-platform/scripts/scale-cluster-*.sh`,
  `k8s/demo-app/keda-scaledobject.yaml` (Task #14).
- Design: [ADR 0005](./adr/0005-keda-over-hpa.md).

## Cluster and workload health

The Platform API computes a 0–100 cluster health score that aggregates node
readiness, pod success rate, warning event count, and deployment
availability. Per-workload health is returned as an error-budget state
(`healthy` / `burning` / `breached`), not as HTTP 200/5xx.

- Implementation: `platform-api/src/routes/health.py`,
  `platform-api/src/slo/`.
- Design: [ADR 0010](./adr/0010-slo-math-over-dashboards.md).

## SLO math

Each workload registers a target and window at creation. The Platform API
computes error budget total / remaining / burn rate and exposes them both
as JSON (`/workloads/{id}/slo`) and as Prometheus gauges
(`platform_slo_error_budget_remaining`, `platform_slo_burn_rate`).

The signal source for the demo is the Platform API's own request counters
— standard Prometheus white-box instrumentation, scraped by the
OpenTelemetry Collector. A production deployment would additionally ingest
ingress / service-mesh metrics over rolling 7- or 30-day windows.

- Implementation: `platform-api/src/slo/model.py`,
  `platform-api/src/slo/store.py`, `platform-api/src/routes/metrics.py`.
- Tests: `platform-api/tests/test_slo_math.py`.

## Observability

SigNoz in place of the Prometheus + Grafana + Loki + Tempo stack because it
is OpenTelemetry-native: metrics, logs, and traces in a single ClickHouse
datastore, so correlation is a click. The OpenTelemetry Collector runs both
as a DaemonSet (per-node host and kubelet stats, logs) and as a singleton
Deployment (cluster-scope object state and events).

- Implementation: `project-01-sre-platform/observability/`,
  `project-01-sre-platform/infrastructure/signoz/`.
- Design: [ADR 0004](./adr/0004-signoz-over-prometheus-grafana.md).

## Secrets and signed operation receipts

The Platform API authenticates to Vault using the Kubernetes auth method —
no static credentials in environment variables or config. Every mutating
operation emits a receipt signed with HMAC-SHA256 using a key sourced from
Vault; the receipt includes `kid`, `trace_id`, `actor`, and before/after
diffs. A standalone CLI verifies receipts offline.

P1 uses a single static bootstrap key and an in-memory receipt buffer,
documented as a known limitation. Production would persist receipts to an
append-only log and rotate the HMAC key with a verification grace window.

- Implementation: `platform-api/src/receipts/`, `platform-api/src/vault/`,
  `project-01-sre-platform/infrastructure/vault/bootstrap.sh`.
- Tests: `platform-api/tests/test_receipts.py`.
- Design: [ADR 0006](./adr/0006-vault-k8s-auth.md),
  [ADR 0009](./adr/0009-hmac-vault-for-receipts.md).

## GitOps and signed container images

Deployments flow through ArgoCD. The cluster state reflects Git; manual
edits drift back automatically. The CI pipeline builds the Platform API
container image and signs it with Sigstore cosign via GitHub OIDC
(keyless — no private key to manage); signatures are pushed alongside
images to GitHub Container Registry.

- Implementation: `project-01-sre-platform/infrastructure/argocd/`,
  `project-01-sre-platform/.github/workflows/ci.yml` (Task #15).
- Design: [ADR 0008](./adr/0008-sigstore-cosign-for-images.md).

## LLM-assisted narrative — opt-in, disabled by default

`/workloads/{id}/explain` can produce a plain-English summary of a
workload's recent events, SLO state, and pod activity. The feature is
gated off by default (`ENABLE_LLM_EXPLAIN=false`) so a fresh clone runs
end-to-end with no external accounts. When enabled, the backend is
selected via `LLM_BACKEND` and supports Gemini (Google AI Studio free
tier) or Ollama (offline, local model). Neither is the default.

- Implementation: `platform-api/src/llm/`,
  `platform-api/src/routes/explain.py`.
- Design: [ADR 0011](./adr/0011-pluggable-llm-backend.md).

## Cost and portability

The entire stack runs on a laptop with Docker. No paid API keys, no
managed services, no account creation beyond GitHub. Tested on Docker
Desktop with 8 GB memory and 14 CPUs allocated; measured peak memory
across the full six-namespace stack is approximately 4.5 GB.
`scripts/cluster-up.sh` completes in about 8 minutes from zero.
