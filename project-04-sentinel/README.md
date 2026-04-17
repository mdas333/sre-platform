# Project 04 — sentinel (planned capstone)

Predictive reliability engineering — the portfolio capstone. Ties Project 01, 02, and 03 together into a single demonstration of what "autonomous reliability" looks like in the open-source world.

## Problem

Even good SRE teams operate reactively: an alert fires, someone investigates, a postmortem is written, and eventually a runbook is updated. The cycle is slow; the signal is local to one incident; knowledge half-lives quickly.

The commercial autonomous-reliability narrative — the pitch NeuBird raised 19.3M against — is to compress this cycle with AI: predict breaches before they happen, generate postmortems automatically from evidence, and keep runbooks living from the incidents that exercised them.

## What this project builds

- **SLO breach forecasting** — uses the error-budget telemetry from Project 01 + historical trends to predict when a workload will breach, with confidence bands.
- **Auto-generated postmortems** — after any `burning` or `breached` state, the Project 02 agent produces a draft postmortem: timeline from receipts + traces, probable root cause, mitigation, lessons. A human reviews and edits; the final version lives in Git.
- **Continuously-learning runbooks** — each time a runbook is used (via the agent or a human), the outcome is recorded. Successful paths are reinforced; dead ends are downranked. The runbook store becomes a living knowledge graph.
- **Executive dashboard** — one page, three numbers: clusters green / burning / breached. The 6 AM Monday view.

## Differentiator

The open-source answer to what NeuBird, Cleric, and Resolve AI are pitching to enterprises. Self-hosted, inspectable, extensible.

## Dependencies

- Projects 01, 02, 03 complete.
- At least 30 days of Project 01 telemetry for the forecasting model baseline.

## Status

Planned. This is the project that justifies a blog post.
