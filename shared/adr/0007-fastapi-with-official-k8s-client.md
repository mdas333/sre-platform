# ADR 0007 — FastAPI and the official Kubernetes Python client

Status: Accepted
Date: 2026-04-16

## Context

The Platform API is an HTTP service that queries the Kubernetes API to read and write workloads, scale deployments, and fetch node state. Two decisions here:

1. Web framework.
2. Kubernetes client library.

A common but lower-signal choice is to shell out to `kubectl` from the API code. This is easy to write but brittle: output parsing is fragile, no type safety, and it cannot stream.

## Decision

- **Framework**: FastAPI. Python 3.12, async-native, Pydantic v2 for request/response validation, automatic OpenAPI generation.
- **Kubernetes client**: the official `kubernetes` PyPI package. All cluster interactions go through its typed API objects. No `subprocess` calls to `kubectl`.

## Consequences

**Upside**

- Typed inputs and outputs; OpenAPI schema is generated from the route definitions and surfaced at `/docs`.
- Async I/O means the Platform API can issue multiple cluster reads concurrently — useful for the `/cluster/health` aggregate call.
- The `kubernetes` client exposes watch streams, which keeps the door open to event-driven features later.

**Downside**

- The `kubernetes` package API is auto-generated from the Kubernetes OpenAPI spec; it's verbose. Wrapping it in small internal helpers (`src/k8s/workloads.py`, `src/k8s/nodes.py`) is done up front to avoid sprawl across routes.

## Alternatives considered

- **Flask** — synchronous; no built-in typing; rejected.
- **Shelling out to `kubectl`** — rejected as non-serious; no production SRE tool works this way.
- **Go with `client-go`** — rejected because Python is a stronger signal for this candidate's existing skills and the rest of the project stays one language.
