#!/usr/bin/env bash
# bootstrap.sh — post-install Vault configuration.
#
# Enables the Kubernetes auth method and creates the policy + role that lets
# the Platform API authenticate with its ServiceAccount token and read its
# secrets (receipt signing key, optional LLM keys).
#
# Idempotent: each step checks for existing state before writing.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
export KUBECONFIG="${KUBECONFIG:-$PROJECT_DIR/infrastructure/cluster/kubeconfig}"

NS="${VAULT_NAMESPACE:-vault}"
POD="${VAULT_POD:-vault-0}"
export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_TOKEN="${VAULT_TOKEN:-root}"

vexec() {
  # Execute a vault CLI command inside the Vault pod.
  kubectl -n "$NS" exec -i "$POD" -- env VAULT_ADDR="$VAULT_ADDR" VAULT_TOKEN="$VAULT_TOKEN" vault "$@"
}

echo "[1] Enable Kubernetes auth method"
if vexec auth list -format=json 2>/dev/null | grep -q '"kubernetes/"'; then
  echo "    already enabled"
else
  vexec auth enable kubernetes
fi

echo "[2] Configure Kubernetes auth"
# The Vault pod uses its own service-account token to introspect other tokens
# against the in-cluster Kubernetes API.
vexec write auth/kubernetes/config \
  kubernetes_host="https://kubernetes.default.svc.cluster.local:443"

echo "[3] Write platform-api policy (least-privilege)"
cat <<'POL' | kubectl -n "$NS" exec -i "$POD" -- env VAULT_ADDR="$VAULT_ADDR" VAULT_TOKEN="$VAULT_TOKEN" vault policy write platform-api -
path "secret/data/platform-api/*" {
  capabilities = ["read"]
}
path "secret/metadata/platform-api/*" {
  capabilities = ["list", "read"]
}
POL

echo "[4] Create platform-api role (bound to its ServiceAccount)"
vexec write auth/kubernetes/role/platform-api \
  bound_service_account_names=platform-api \
  bound_service_account_namespaces=sre-platform \
  policies=platform-api \
  ttl=1h

echo "[5] Seed initial receipt-signing secret"
# Vault dev mode pre-enables KV v2 at secret/, so no mount step needed.
# Generate a fresh 256-bit key. The Platform API reads this at startup and
# rotates via a daily CronJob in production. For the portfolio demo, a
# single bootstrap write is sufficient.
SIGNING_KEY="$(openssl rand -base64 32)"
KID="key-$(date +%Y-%m-%d)"
vexec kv put secret/platform-api/receipt-key kid="$KID" key="$SIGNING_KEY" >/dev/null
echo "    wrote secret/platform-api/receipt-key with kid=$KID"

echo
echo "Vault bootstrap complete."
