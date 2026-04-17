# platform-api

The FastAPI service that surfaces the Platform API for Project 01 — the developer-facing product built on top of the Kubernetes cluster.

See [`../README.md`](../README.md) for the full architecture, endpoint list, and design decisions.

## Local development

```bash
cd platform-api
uv sync
uv run pytest -v
uv run ruff check src tests
uv run uvicorn src.main:app --reload --port 8080
```

OpenAPI docs: http://localhost:8080/docs

## Configuration

All runtime configuration is driven by environment variables, bound via `pydantic-settings` in `src/config.py`. The important ones:

| Variable | Default | Purpose |
|---|---|---|
| `PLATFORM_API_LOG_LEVEL` | `INFO` | Log verbosity |
| `PLATFORM_API_OTLP_ENDPOINT` | `http://signoz-otel-collector.signoz.svc.cluster.local:4317` | Where to send OTel signals |
| `PLATFORM_API_VAULT_ADDR` | `http://vault.vault.svc.cluster.local:8200` | Vault endpoint |
| `PLATFORM_API_VAULT_ROLE` | `platform-api` | Vault Kubernetes auth role |
| `LLM_BACKEND` | `gemini` | `gemini`, `ollama`, or `claude` |
| `ENABLE_LLM_EXPLAIN` | `false` | Gate the `/explain` endpoint |
| `GOOGLE_API_KEY` | — | Required when `LLM_BACKEND=gemini` |
| `OLLAMA_ENDPOINT` | `http://host.docker.internal:11434` | Ollama base URL |

## Layout

```
src/
├── main.py              # FastAPI app composition
├── config.py            # pydantic-settings
├── telemetry.py         # OTel wiring
├── k8s/                 # Kubernetes client helpers
├── vault/               # Vault client
├── slo/                 # SLO math (pure functions + tests)
├── receipts/            # HMAC sign / verify
├── llm/                 # Pluggable LLM backends
└── routes/              # FastAPI routers
```
