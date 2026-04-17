# Project 02 — ai-sre-agent (planned)

An agentic SRE assistant that investigates and remediates incidents on the platform built in Project 01.

## Problem

Incident response today is mostly manual: a human on-call reads alerts, opens dashboards, correlates traces, forms hypotheses, and runs kubectl commands. Commercial products (Cleric, NeuBird Hawkeye, Resolve AI, Datadog Bits AI) automate this, but they are closed SaaS. The open-source landscape is thin.

## What this project builds

A self-hosted AI SRE agent that consumes Project 01's Platform API and telemetry to investigate incidents autonomously.

- **MCP server** — exposes Project 01's Platform API and SigNoz query interface as typed tools: `get_workload_slo`, `get_recent_events`, `query_traces`, `query_logs`, `describe_workload`, `propose_scale`.
- **Agent** — an LLM orchestrator (Claude by default, configurable to Gemini) that takes an incident signal as input, reasons across the tools, and produces a structured root-cause hypothesis with cited evidence and a suggested remediation.
- **Web UI** — streams the agent's reasoning in real time, so an on-call engineer can watch it think and intervene before any action is taken.
- **Guardrails** — remediation proposals are never executed automatically. The agent surfaces them; a human approves.

## Differentiator

Most AI SRE tooling is either a chat interface over logs or a fully-closed-source SaaS. Project 02 is a self-hosted, Kubernetes-native reference implementation that a company could actually deploy inside their VPC.

## Dependencies

- Project 01 must be running (cluster, Platform API, SigNoz, Vault).
- One LLM key: Gemini free-tier (default) or Claude paid.

## Status

Planned. Design brief and MCP tool list will land here when Project 01 is complete.
