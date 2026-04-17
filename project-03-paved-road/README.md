# Project 03 — paved-road (planned)

Multi-environment GitOps on top of the Project 01 platform. The "paved road" is the opinionated happy path every workload takes — dev, staging, production — with policy, secrets, and consistency handled by the platform, not by each team.

## Problem

Project 01 is a single-cluster demo. Real platform engineering spans multiple environments and enforces consistency across them. A workload should behave the same way in dev and production with a single manifest, differentiated only by values.

## What this project builds

- **Three k3d clusters** — `dev`, `staging`, `prod` — plus an ArgoCD hub cluster that manages all three.
- **App-of-Apps pattern** — each environment is an ArgoCD Application that spawns child Applications per workload. Promotion is a directory move in Git.
- **Helm chart library** — a reusable `platform-workload` chart that encodes the conventions (labels, resource limits, probes, OTel SDK config). Teams ship values files, not templates.
- **Policy-as-code** — OPA Gatekeeper and Kyverno admission policies: all pods must carry owner labels, all images must be cosign-verified, no `privileged: true`.
- **Secrets in Git** — SOPS-encrypted values files in the repo. The decryption key lives in Vault (per environment).
- **Progressive delivery** — Argo Rollouts for canary deployment to production.

## Differentiator

Most "GitOps portfolio" projects stop at "ArgoCD syncs a manifest". Project 03 is the step up: multi-env, policy-gated, progressive-delivery, with encrypted secrets in Git. That is what a real platform team runs.

## Dependencies

- Project 01's cluster lifecycle scripts (extended to multi-cluster).
- Project 01's Platform API (used as the example workload deployed across environments).

## Status

Planned.
