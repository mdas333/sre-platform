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

Use Sigstore cosign with key-based signing in Project 01. The signing key pair is generated once and stored in Vault. CI uses the same key via a secret injected into the GitHub Actions runner. Signatures are pushed alongside images to GitHub Container Registry.

A future evolution to keyless cosign (Fulcio + Rekor) in CI is documented as a Project 03 extension.

## Consequences

**Upside**

- Signed images are verifiable offline. The CI produces a `cosign verify` step as part of its own pipeline — any tampered image fails verification.
- Cosign is the supply-chain-signing tool with real adoption.

**Downside**

- Key-based cosign requires key management. The portfolio uses Vault for this, which is consistent with ADR 0006.
- Keyless cosign is the direction of the ecosystem; moving to it is on the Project 03 roadmap.

## Related

- ADR 0009 (why HMAC, not cosign, is used for operational receipts).
