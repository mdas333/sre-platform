"""
Shared singletons for routes — avoids a global registry per-router.

Constructed lazily so importing any router is cheap; the actual SLO
store and receipt emitter come to life on first use.
"""

from __future__ import annotations

import logging
import os
import threading

from receipts.emitter import ReceiptEmitter
from slo.store import SLOStore

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_slo_store: SLOStore | None = None
_emitter: ReceiptEmitter | None = None


def get_slo_store() -> SLOStore:
    global _slo_store
    with _lock:
        if _slo_store is None:
            _slo_store = SLOStore()
    return _slo_store


def _dev_key_provider():
    """Dev fallback: a static key from env, rotated manually."""
    kid = os.environ.get("RECEIPT_KID", "dev-key-0")
    key = os.environ.get("RECEIPT_KEY_B64")
    if key:
        import base64
        return kid, base64.b64decode(key)
    return kid, b"dev-placeholder-key-32bytes-xxxxxxx"[:32]


def get_emitter() -> ReceiptEmitter:
    """
    Build the emitter. In-cluster it reads the current key from Vault; in
    dev it falls back to an env-provided key or a static placeholder so
    the server still starts.
    """
    global _emitter
    with _lock:
        if _emitter is None:
            key_provider = _dev_key_provider
            try:
                from config import get_settings
                from vault.client import VaultClient

                vault = VaultClient()
                if vault.is_authenticated():
                    def key_provider():  # type: ignore[no-redef]
                        data = vault.read_kv(get_settings().receipt_key_path)
                        import base64
                        return data["kid"], base64.b64decode(data["key"])
            except Exception:
                logger.warning(
                    "Vault receipt-key provider unavailable; using dev key fallback",
                    exc_info=True,
                )
            _emitter = ReceiptEmitter(key_provider=key_provider)
    return _emitter
