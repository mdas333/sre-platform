# Talking points

Claims backed by code in this repository. Each point maps to an artifact under `project-01-sre-platform/` or `shared/`. Organised by theme.

## Cluster lifecycle

- Kubernetes cluster lifecycle is managed declaratively with OpenTofu and the `kreuzwerker/k3d` provider — a single server and three agents, stood up and torn down from one script.
- State is a Git artifact, not something that drifts: `tofu plan` shows any drift immediately.

## Scaling

- Two layers of scaling are implemented and demonstrated:
  - Cluster-level: adding an agent node and draining + removing one, scripted in `scripts/scale-cluster-up.sh` and `scripts/scale-cluster-down.sh`.
  - Workload-level: KEDA with the HTTP add-on drives Platform API pods from zero under load and back to zero after idle.
- Scale-to-zero is a genuine cost pattern — it is rare in portfolios and visible on the scaling GIF.

## Health and SLOs

- The Platform API computes a 0–100 cluster health score that aggregates node readiness, pod success rate, warning event count, and deployment availability. This is a custom metric that no off-the-shelf tool provides.
- SLO math is first-class: each workload registers a target and window at create time. The Platform API computes error budget remaining and burn rate and exposes both as JSON (`/workloads/{id}/slo`) and as a Prometheus metric (`platform_slo_error_budget_remaining_seconds`).
- The `/health` endpoint is error-budget-aware — it returns `state: "healthy" | "burning" | "breached"`, not just HTTP 200. That is the senior-level reliability signal.

## Observability

- SigNoz is used in place of the Prometheus + Grafana + Loki + Tempo stack because it is OpenTelemetry-native. Metrics, logs, and traces sit in a single ClickHouse datastore, which means correlation is a click, not a tool switch.
- The OpenTelemetry Collector is deployed with `k8s_cluster`, `kubeletstats`, `hostmetrics`, OTLP gRPC, and `filelog` receivers — five distinct signal sources funnelled through one pipeline.
- The Platform API is fully OTel-instrumented — request traces, custom SLO metrics, health score, and receipt events are all correlated by `trace_id`.

## Security and signed receipts

- The Platform API authenticates to Vault using the Kubernetes auth method — no static credentials in env vars or config files. The Vault policy is least-privilege, granting read access only to `secret/data/platform-api/*`.
- Every mutating operation (`POST /workloads`, `POST /scale`, `DELETE /workloads/{id}`) emits a receipt signed with HMAC-SHA256 using a key rotated daily from Vault.
- Receipts are queryable via `/audit` and verifiable offline by a standalone CLI (`scripts/verify-receipt`).
- Container images are signed with Sigstore cosign in the CI pipeline; the signature is pushed alongside the image to GHCR.

## GitOps and CI

- Deployments flow through ArgoCD. The cluster state reflects Git; if someone manually changes a resource, ArgoCD drifts it back.
- CI runs lint → test → container build → cosign sign → push to GHCR on every push to `main`. ArgoCD picks up the new image and syncs the cluster automatically.
- The full CI pipeline is defined in `project-01-sre-platform/.github/workflows/ci.yml` — under 120 lines.

## AI, used tastefully

- The Platform API's `/workloads/{id}/explain` endpoint summarises recent events, SLO status, and pod state into a plain-English paragraph.
- The underlying LLM is pluggable — `GeminiBackend` is the default (Google AI Studio free tier), `OllamaBackend` is the offline fallback, and `ClaudeBackend` is a stub enabled in Project 02.
- The feature is gated off by default. A fresh clone runs end-to-end without an LLM key.

## Cost and portability

- The entire stack runs on a personal laptop with Docker. No paid API keys, no managed services, no account creation beyond GitHub.
- Quick-start completes in under 10 minutes from a fresh clone on a machine with Homebrew and Docker available.
- Total cost: zero.
