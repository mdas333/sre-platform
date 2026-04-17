# Glossary

Short definitions for the vocabulary used across this portfolio. Aimed at readers who may know some terms but not all of them.

## Reliability engineering

- **SRE (Site Reliability Engineering)** — an engineering discipline that applies software-engineering practices to operations. Treats reliability as a feature with measurable targets.
- **Platform Engineering** — building internal developer platforms that let application teams ship without wrestling with infrastructure. The "customer" is the developer.
- **SLI (Service Level Indicator)** — a measurable property of a service, e.g. HTTP success rate, request latency.
- **SLO (Service Level Objective)** — a target for an SLI, e.g. 99.9% success rate over a rolling 7-day window.
- **SLA (Service Level Agreement)** — a contract with consequences when SLOs are missed. External.
- **Error budget** — `(1 − SLO) × total_events`. The amount of failure permitted before the SLO is breached.
- **Burn rate** — how fast the error budget is being consumed, relative to a sustainable rate.
- **MTTR / MTTD / MTBF** — mean time to recovery / detection / between failures.
- **Golden signals (RED, USE)** — frameworks for choosing what to measure. RED: Rate, Errors, Duration (for request-driven services). USE: Utilisation, Saturation, Errors (for resources).

## Kubernetes

- **Pod** — smallest deployable unit, one or more containers sharing a network namespace.
- **Deployment** — a controller that maintains a desired number of pod replicas.
- **Service** — a stable network endpoint in front of a set of pods.
- **Namespace** — a logical partition within a cluster.
- **ServiceAccount** — pod identity used by RBAC and external auth systems.
- **ConfigMap / Secret** — mounted or env-injected configuration. Secrets are base64-encoded, not encrypted at rest by default.
- **HPA (Horizontal Pod Autoscaler)** — scales pod replicas based on CPU/memory or custom metrics.
- **VPA (Vertical Pod Autoscaler)** — right-sizes resource requests.
- **Control plane** — API server, scheduler, controller manager, etcd. The brain.
- **Data plane** — kubelet + container runtime on worker nodes. The muscle.

## Platform tooling in this repository

- **k3d** — runs k3s (CNCF-certified minimal Kubernetes) inside Docker containers; supports multi-node clusters on a laptop.
- **OpenTofu** — open-source, Linux-Foundation-governed fork of Terraform. Identical HCL, MPL 2.0 licensed.
- **Vault (dev mode)** — HashiCorp Vault running as a single binary; stores secrets and mints short-lived credentials.
- **SigNoz** — OpenTelemetry-native observability platform backed by ClickHouse. Unifies metrics, logs, and traces.
- **OpenTelemetry / OTLP** — vendor-neutral telemetry standard; OTLP is its wire protocol.
- **KEDA** — Kubernetes Event-Driven Autoscaling. Scales pods on any external signal, including scale-to-zero.
- **ArgoCD** — GitOps controller: watches a Git repository and reconciles the cluster to match.
- **Sigstore cosign** — signs and verifies container images. Keyless mode uses OIDC; key-based mode uses local keys.

## Security and delivery

- **GitOps** — declarative operations where Git is the source of truth and a controller reconciles reality to Git.
- **Admission controller** — intercepts API-server writes to apply policy (OPA Gatekeeper, Kyverno).
- **OCI (Open Container Initiative)** — standards body for container images and runtimes.
- **SBOM (Software Bill of Materials)** — list of components inside a container image or application.

## Scaling patterns

- **Scale-to-zero** — a workload with zero replicas when idle; the first request wakes it. Common in serverless and HTTP-autoscaled systems.
- **Cluster autoscaler** — adds or removes cluster nodes based on unschedulable pods and unused capacity.
- **Request-rate autoscaling** — scales replicas based on incoming traffic, not CPU. Often fronted by a gateway that queues during cold start.
