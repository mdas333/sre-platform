"""
HMAC-signed operation receipts.

Every mutating operation on the Platform API emits a receipt that is
HMAC-SHA256 signed with a rotating key sourced from Vault. Receipts are
verifiable offline by a standalone CLI that only needs the public set of
signing keys (by key ID).

Canonical JSON — sorted keys, no whitespace — ensures signatures over the
same logical content are byte-identical regardless of dict ordering in
the source code. This matters because Python preserves insertion order
but producers may construct receipts in different orders.

See shared/adr/0009-hmac-vault-for-receipts.md for the rationale on HMAC
over cosign for in-band operation signatures.
"""

from __future__ import annotations

import base64
import hmac
import json
from collections.abc import Callable
from hashlib import sha256
from typing import Any


def canonical_json(payload: dict[str, Any]) -> bytes:
    """Deterministic JSON: sorted keys, compact separators, UTF-8."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def _payload_without_hmac(receipt: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in receipt.items() if k != "hmac"}


def sign(receipt: dict[str, Any], key: bytes) -> dict[str, Any]:
    """
    Return a copy of the receipt with an `hmac` field appended.

    The `kid` field must already be set on the receipt so a verifier can
    locate the correct key; callers that omit `kid` will get a receipt
    that fails verification later.
    """
    payload = canonical_json(_payload_without_hmac(receipt))
    digest = hmac.new(key, payload, sha256).digest()
    return {**_payload_without_hmac(receipt), "hmac": base64.b64encode(digest).decode("ascii")}


KeyResolver = Callable[[str], bytes]
"""Callable that takes a `kid` and returns the corresponding raw key bytes.
Should raise KeyError if the kid is unknown."""


def verify(receipt: dict[str, Any], resolver: KeyResolver) -> bool:
    """
    Constant-time verify.

    Returns False on any failure: missing `hmac`, unknown `kid`, bad
    base64, or signature mismatch. Never raises on valid input shapes.
    """
    raw_hmac = receipt.get("hmac")
    kid = receipt.get("kid")
    if not isinstance(raw_hmac, str) or not isinstance(kid, str):
        return False
    try:
        provided = base64.b64decode(raw_hmac, validate=True)
        key = resolver(kid)
    except (ValueError, KeyError):
        return False
    payload = canonical_json(_payload_without_hmac(receipt))
    expected = hmac.new(key, payload, sha256).digest()
    return hmac.compare_digest(provided, expected)
