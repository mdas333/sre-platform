# ADR 0002 — k3d for local Kubernetes

Status: Accepted
Date: 2026-04-16

## Context

Project 01 requires a local Kubernetes cluster that can demonstrate:

- Multi-node topology realistic enough to reflect production (one server, multiple agents).
- Node-level scaling: adding an agent, draining and removing one.
- Fast spin-up and teardown so recruiters can run `cluster-up.sh` in under ten minutes.

Candidates considered: Minikube, Kind, MicroK8s, k3d.

## Decision

Use k3d: runs k3s (a CNCF-certified, production-grade Kubernetes distribution) inside Docker containers. Topology: one server node and three agent nodes.

## Consequences

**Upside**

- Multi-node out of the box without virtual machines.
- `k3d node create` adds an agent to a running cluster — exactly the operation needed for the scale-up demo.
- Start-up time is seconds, not minutes.
- Uses real k3s, which is production-grade and used in the real world by many teams.

**Downside**

- Not identical to upstream Kubernetes — k3s ships with flannel, servicelb, and traefik by default. Where the project needs upstream behaviour (e.g. no built-in load balancer for the KEDA HTTP add-on test), the k3d config disables these explicitly.

## Alternatives considered

- **Kind** — single-node by default; multi-node is possible but awkward. Scale demos feel contrived.
- **Minikube** — VM-backed; slower to start, heavier, and node lifecycle is not a first-class operation.
- **MicroK8s** — Linux-centric; macOS story is worse than k3d.
