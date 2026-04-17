# sre-platform

An internal developer platform on Kubernetes, with SRE-grade reliability engineering built in — not bolted on.

## What this is

A working portfolio: a platform engineering + site reliability engineering project on Kubernetes, plus a planned arc of three follow-on projects. Everything here is free to run, runs on a single laptop with Docker, and is designed to be read end-to-end in one sitting.

Project 01 demonstrates:

- Declarative Kubernetes cluster lifecycle with OpenTofu.
- Two layers of scaling — cluster nodes, plus workload pods with scale-to-zero on a separate demo workload (the Platform API itself stays always-on).
- A developer-facing Platform API with error-budget-aware health and SLO math.
- HMAC-signed audit receipts for every platform operation, verifiable offline.
- OpenTelemetry-native observability (SigNoz) across metrics, logs, and traces.
- GitOps deployment via ArgoCD; container images signed in CI with Sigstore cosign (keyless, via GitHub OIDC).
- An optional, disabled-by-default LLM adapter that summarises workload state in plain English.

Project 01 optimises for **breadth** — every component a platform team typically integrates, brought up at laptop scale. Project 03 revisits the same pieces in a paved-road, multi-environment form.

## Project arc

| # | Project | Theme | Status |
|---|---------|-------|--------|
| 01 | [`sre-platform`](./project-01-sre-platform/) | Platform API + SLO math + signed receipts on k3d | In progress |
| 02 | [`ai-sre-agent`](./project-02-ai-sre-agent/) | Agentic SRE assistant built on top of Project 01 | Planned |
| 03 | [`paved-road`](./project-03-paved-road/) | Multi-environment GitOps with policy-as-code | Planned |
| 04 | [`sentinel`](./project-04-sentinel/) | Predictive reliability capstone | Planned |

## Navigation

- [`shared/`](./shared/) — cross-project knowledge: architecture decision records, glossary, a capabilities index, reusable OpenTofu modules, bootstrap scripts.
- [`project-XX-*/`](.) — each project is self-contained with its own README, infrastructure, application code, tests, and documentation. Project 01 is the primary artifact.

## Quick start (project 01)

Prerequisites: Docker Desktop running, Homebrew available.

Tested on Docker Desktop with 8 GB memory and 14 CPUs; the full stack's measured peak memory is approximately 4.5 GB.

```bash
./shared/scripts/preflight.sh           # verify local tooling
cd project-01-sre-platform
./scripts/cluster-up.sh                 # full stack in ~8 min
./scripts/demo.sh                       # narrated walkthrough
```

## Author

**Moulima Das** — DevOps / SRE engineer with six years of production Kubernetes experience. Open to remote Senior SRE / Platform Engineer roles.

GitHub: [mdas333](https://github.com/mdas333)

## License

MIT — see [LICENSE](./LICENSE).
