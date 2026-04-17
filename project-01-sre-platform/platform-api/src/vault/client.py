"""
Vault client — Kubernetes auth method.

Authenticates using the pod's own ServiceAccount token (no static
credentials). Fetches secrets via KV v2. In dev (outside the cluster)
falls back to `VAULT_TOKEN` env var.

See shared/adr/0006-vault-k8s-auth.md.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import hvac

from config import get_settings

logger = logging.getLogger(__name__)


class VaultClient:
    def __init__(self) -> None:
        s = get_settings()
        self._client = hvac.Client(url=s.vault_addr)
        self._authenticate(s)

    def _authenticate(self, s) -> None:
        jwt_path = Path(s.vault_token_path)
        if jwt_path.exists():
            # Kubernetes auth using the pod's SA token.
            jwt = jwt_path.read_text().strip()
            self._client.auth.kubernetes.login(role=s.vault_role, jwt=jwt, mount_point=s.vault_k8s_mount)
            logger.info("Vault: authenticated via Kubernetes auth (role=%s)", s.vault_role)
            return

        token = os.environ.get("VAULT_TOKEN")
        if token:
            self._client.token = token
            logger.info("Vault: authenticated via VAULT_TOKEN env (dev mode)")
            return

        logger.warning("Vault: no credentials available; reads will fail")

    def is_authenticated(self) -> bool:
        try:
            return bool(self._client.is_authenticated())
        except Exception:
            return False

    def read_kv(self, path: str) -> dict:
        """Read a KV v2 secret at `secret/data/<path>`. Returns the data dict."""
        resp = self._client.secrets.kv.v2.read_secret_version(path=path)
        return resp["data"]["data"]
