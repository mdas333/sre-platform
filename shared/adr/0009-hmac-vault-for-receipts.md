# ADR 0009 — HMAC with Vault-managed keys for operation receipts

Status: Accepted
Date: 2026-04-16

## Context

Every mutating operation on the Platform API (workload creation, scale, deletion) must produce an audit receipt that:

- Is signed, so the receipt cannot be forged by a reader of the audit log.
- Is verifiable offline by a small standalone tool.
- Links to a trace ID so receipts can be correlated with telemetry in SigNoz.
- Has a key that can be rotated.

An option considered was Sigstore cosign. Cosign, however, is designed for signing artifacts at rest (images, SBOMs, blobs) — not for in-band event signatures embedded in a service's data path. Every receipt would pay the cosign CLI's startup cost and require a full PKI round-trip. That is the wrong instrument.

## Decision

Sign receipts with HMAC-SHA256, using a 256-bit key managed by Vault. The key is rotated daily; the Platform API accepts both the current and the previous key ID during a grace window.

Receipt structure (canonical JSON, sorted keys):

```json
{
  "op_id": "01J2...",
  "ts": "2026-04-16T18:22:11Z",
  "actor": "platform-api@sre-platform",
  "action": "scale",
  "workload_id": "demo-app",
  "before": { "replicas": 2 },
  "after":  { "replicas": 5 },
  "trace_id": "4bf92f35...",
  "kid": "key-2026-04-16",
  "hmac": "BASE64(HMAC-SHA256(signing_key, canonical_json_without_hmac_field))"
}
```

A standalone verifier at `scripts/verify-receipt` reads a JSON receipt on stdin and a key (or key ID) from Vault, then prints `VERIFIED` or `INVALID`.

## Consequences

**Upside**

- Right tool for the job. HMAC is fast, simple, and auditable.
- Rotatable. The verifier accepts multiple `kid`s.
- Small surface area: one Python module for the signer, one for the verifier.

**Downside**

- HMAC is symmetric; anyone with the signing key can forge receipts. Access to the key is restricted to the Platform API's Vault role, and Vault's own audit log captures every read.
- For a public audit story a asymmetric signature would be stronger. That is on the Project 04 roadmap when the signed artifact is exposed externally.

## Related

- ADR 0006 (Vault Kubernetes auth) — how the Platform API gets the signing key.
- ADR 0008 (cosign) — covers image signing; complementary, not overlapping.
