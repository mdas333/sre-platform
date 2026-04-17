# ADR 0006 — Vault Kubernetes auth for the Platform API

Status: Accepted
Date: 2026-04-16

## Context

The Platform API needs secrets: a signing key for operation receipts, and any API keys for optional integrations (Gemini, Ollama endpoint). Options:

1. Environment variables injected from a Kubernetes `Secret`. Simple, but credentials are static and visible in `kubectl describe`.
2. Mounted files from a `Secret`. Same properties as (1).
3. External secrets operator that syncs from a secret manager. Adds a controller; still static credentials from the pod's perspective.
4. Vault with the Kubernetes auth method — the pod uses its ServiceAccount token to obtain a short-lived Vault token, which it uses to read secrets.

Option (4) is how production SRE environments handle this.

## Decision

Deploy HashiCorp Vault in dev mode in the cluster. The Platform API authenticates using the Kubernetes auth method, via the service account token auto-mounted at `/var/run/secrets/kubernetes.io/serviceaccount/token`. A least-privilege Vault policy grants read-only access to `secret/data/platform-api/*`.

## Consequences

**Upside**

- No static credentials in the pod. The bootstrap flow is token-free.
- The signing key for receipts can be rotated by updating Vault and rolling the Platform API — no secret-sync lag.
- Vault usage is a genuine production pattern; every SRE interviewer recognises it.

**Downside**

- Vault dev mode is ephemeral: a restart loses all secrets. Acceptable for a portfolio demo; a production setup would use `raft` storage and auto-unseal.
- The bootstrap script must enable the Kubernetes auth method, write the policy, and create the role before the Platform API pod starts. The script handles this idempotently.
