## v0.1.0 — Project 01 (`sre-platform`)

First tagged release of the `sre-platform` portfolio arc. Project 01 is complete: the platform comes up end-to-end on a single laptop, every layer is signed, and every claim in the README is backed by working code.

### What's in this release

**Infrastructure** — 4-node k3d cluster (1 server + 3 agents) provisioned declaratively with OpenTofu; idempotent create / destroy; scale-up and scale-down scripts verified live (4 ↔ 5 nodes).

**Platform dependencies** — Vault (dev mode with the Kubernetes auth method bootstrapped), ArgoCD (reconciling the `k8s/` tree from `main`), KEDA (cron-triggered scale-to-zero on a tenant workload), SigNoz (OpenTelemetry-native, ClickHouse-backed), and a two-collector OpenTelemetry pipeline (DaemonSet for per-node stats + singleton Deployment for cluster-scope events). All chained in `scripts/cluster-up.sh`.

**Platform API** — 17 FastAPI routes exposing a developer-facing platform surface: `POST /workloads` with declared SLO targets, `GET /workloads/{id}/health` returning error-budget state, `GET /workloads/{id}/slo` returning the full math, `POST /workloads/{id}/scale` emitting a signed audit receipt, `GET /audit` for the signed operation log, `GET /cluster/health` as an aggregate 0-100 score, and `/metrics` as a Prometheus scrape endpoint. 31 unit tests pass; `ruff` clean.

**Three layers of signed provenance**
- Commits are SSH-signed and carry GitHub's "Verified" badge.
- Container images are signed with **keyless cosign** via GitHub Actions OIDC — no private key to manage, rotate, or leak. `scripts/verify-image.sh` pins verification to this repo's `ci.yml` workflow.
- Every mutating Platform API operation emits a canonical-JSON receipt signed with HMAC-SHA256 using a Vault-sourced key. `scripts/verify-receipt` validates offline.

**Delivery** — GitHub Actions runs lint + tests + kubeconform + buildx + cosign sign + GHCR push on every commit to `main`. ArgoCD reconciles the resulting image; its `sre-platform` Application reports **Synced / Healthy** across 12 resources.

**Documentation** — a 13-chapter beginner-friendly [`WALKTHROUGH.md`](./project-01-sre-platform/docs/WALKTHROUGH.md) with 7 Mermaid diagrams, live command outputs, and four integrated proof screenshots (Docker Desktop, ArgoCD, SigNoz, GitHub Actions). Eleven ADRs, one per real trade-off. A capabilities index, a glossary, and two recorded GIFs (cluster-level scale and KEDA scale-to-zero).

### Known P1 limitations (each paired with its production path)

- `/workloads` has no auth, quota, or admission policy. Production path: bearer-token middleware + OPA/Kyverno admission (Project 03).
- Receipts live in an in-memory buffer of the last 200 entries. Production path: append-only log or ClickHouse via SigNoz — see [ADR 0009](./shared/adr/0009-hmac-vault-for-receipts.md).
- Single static HMAC signing key (no rotation). Production path: daily CronJob rotation with grace window; the verifier already accepts multiple `kid` values.
- Vault runs in dev mode (ephemeral). Production path: raft storage with auto-unseal — see [ADR 0006](./shared/adr/0006-vault-k8s-auth.md).
- `metrics-server` disabled in k3d config to save RAM. Production path: re-enable for live HPA CPU scaling.
- KEDA trigger is cron for reproducible demo. Production path: HTTP-rate, Prometheus, Kafka, or SQS triggers depending on the workload — see [ADR 0005](./shared/adr/0005-keda-over-hpa.md).
- The `/explain` LLM endpoint is off by default. Opt-in Gemini (Google AI Studio free tier) or offline Ollama — see [ADR 0011](./shared/adr/0011-pluggable-llm-backend.md).

### What's next in the arc

- **Project 02 — `ai-sre-agent`**: an agentic SRE assistant that consumes Project 01's Platform API and SigNoz telemetry to investigate incidents.
- **Project 03 — `paved-road`**: multi-environment GitOps with policy-as-code, promotion via App-of-Apps, SOPS-encrypted secrets, and Argo Rollouts.
- **Project 04 — `sentinel`**: predictive SLO-breach detection, auto-generated postmortems, continuously-learning runbooks.

### Verify what landed

```bash
cosign verify \
  --certificate-identity-regexp '^https://github\.com/mdas333/sre-platform/\.github/workflows/ci\.yml@refs/heads/.*' \
  --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
  ghcr.io/mdas333/sre-platform/platform-api:main
```

---

Author: Moulima Das ([mdas333](https://github.com/mdas333))
License: MIT
