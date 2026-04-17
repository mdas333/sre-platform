"""Tests for HMAC receipt signing and verification."""

from __future__ import annotations

import base64

from receipts.signer import canonical_json, sign, verify

KEY_A = b"\x01" * 32
KEY_B = b"\x02" * 32

KEYS = {"key-a": KEY_A, "key-b": KEY_B}


def resolver_strict(kid: str) -> bytes:
    return KEYS[kid]


def base_receipt(**overrides):
    r = {
        "op_id": "01J2HR5FAKE",
        "ts": "2026-04-18T00:00:00Z",
        "actor": "platform-api@sre-platform",
        "action": "scale",
        "workload_id": "demo-app",
        "before": {"replicas": 2},
        "after": {"replicas": 5},
        "trace_id": "4bf92f35abc",
        "kid": "key-a",
    }
    r.update(overrides)
    return r


def test_canonical_json_is_order_independent():
    assert canonical_json({"b": 2, "a": 1}) == canonical_json({"a": 1, "b": 2})


def test_canonical_json_is_deterministic_bytes():
    expected = b'{"a":1,"b":[1,2],"c":"x"}'
    assert canonical_json({"c": "x", "a": 1, "b": [1, 2]}) == expected


def test_sign_adds_hmac_field():
    signed = sign(base_receipt(), KEY_A)
    assert "hmac" in signed
    # the value is valid base64
    base64.b64decode(signed["hmac"], validate=True)


def test_sign_is_idempotent_for_same_input():
    r = base_receipt()
    assert sign(r, KEY_A)["hmac"] == sign(r, KEY_A)["hmac"]


def test_verify_round_trip():
    signed = sign(base_receipt(), KEY_A)
    assert verify(signed, resolver_strict) is True


def test_verify_fails_with_wrong_key():
    signed = sign(base_receipt(kid="key-a"), KEY_B)  # signed with B but labelled A
    assert verify(signed, resolver_strict) is False


def test_verify_fails_when_field_tampered():
    signed = sign(base_receipt(), KEY_A)
    signed["after"] = {"replicas": 99}
    assert verify(signed, resolver_strict) is False


def test_verify_fails_when_hmac_missing():
    r = base_receipt()
    assert verify(r, resolver_strict) is False


def test_verify_fails_for_unknown_kid():
    signed = sign(base_receipt(kid="unknown-kid"), KEY_A)
    assert verify(signed, resolver_strict) is False


def test_verify_fails_on_malformed_hmac():
    signed = sign(base_receipt(), KEY_A)
    signed["hmac"] = "!!not base64!!"
    assert verify(signed, resolver_strict) is False


def test_multiple_kids_supported():
    """Rotation scenario: old key-a receipt and new key-b receipt coexist."""
    old = sign(base_receipt(kid="key-a"), KEY_A)
    new = sign(base_receipt(kid="key-b", op_id="NEW"), KEY_B)
    assert verify(old, resolver_strict)
    assert verify(new, resolver_strict)


def test_resolver_raising_keyerror_is_treated_as_unknown():
    def resolver(kid: str) -> bytes:
        raise KeyError(kid)

    signed = sign(base_receipt(), KEY_A)
    assert verify(signed, resolver) is False
