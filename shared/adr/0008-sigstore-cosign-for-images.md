# ADR 0008 — Sigstore cosign for container image signing

Status: Accepted
Date: 2026-04-16

## Context

Supply chain security is a 2025–2026 focus area across the industry. The minimum bar for a serious portfolio project is: images pushed to a registry are signed, and signatures can be verified.

Options:

1. No signing. Unacceptable for this project's positioning.
2. Docker Content Trust (Notary v1). Largely abandoned in the ecosystem.
3. Sigstore cosign with a local key pair. Simple, no external dependencies.
4. Sigstore cosign keyless (OIDC-backed). Requires an OIDC provider — GitHub Actions provides one, which works for CI; it does not work for local pushes.

## Decision

Use Sigstore cosign with **keyless signing** driven by GitHub Actions' OIDC identity. The CI workflow requests an OIDC token from GitHub (`id-token: write`), cosign signs the image using that token, and Fulcio issues a short-lived certificate recorded in the Rekor transparency log. Signatures are pushed alongside images to GitHub Container Registry. No long-lived private key is ever generated, stored, or rotated.

For local development, images stay unsigned — local `docker build` output is consumed directly by `k3d image import` without going through a registry. Only CI-produced images land in GHCR, and only those are signed.

## Consequences

**Upside**

- No key to manage, rotate, or leak. The signing identity is the workflow run itself, which has a cryptographically verifiable ancestry (repo + commit + ref + actor).
- Verification is repo-scoped: `cosign verify --certificate-identity-regexp ".*mdas333/sre-platform.*" --certificate-oidc-issuer "https://token.actions.githubusercontent.com"` checks the image was built by this repo's CI.
- Rekor transparency log provides a public audit trail without the portfolio needing to run its own.

**Downside**

- Local push-to-registry workflows cannot sign (there is no OIDC identity outside CI). The workaround of `k3d image import` for local testing is documented in `scripts/cluster-up.sh`.
- Keyless verification policies can be verbose; provide a `scripts/verify-image.sh` helper.

## Related

- ADR 0009 (why HMAC, not cosign, is used for operational receipts).
