#!/usr/bin/env bash
# cluster-up.sh — bring up the full Project 01 environment.
#
# Idempotent: re-running is safe. If the cluster already exists, OpenTofu's
# create provisioner short-circuits.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CLUSTER_DIR="$PROJECT_DIR/infrastructure/cluster"

echo "[1] Provision k3d cluster via OpenTofu"
cd "$CLUSTER_DIR"
tofu init -input=false -no-color
tofu apply -auto-approve -input=false -no-color

export KUBECONFIG="$CLUSTER_DIR/kubeconfig"
echo
echo "[2] Wait for all nodes to be Ready"
kubectl wait --for=condition=Ready node --all --timeout=180s

echo
echo "---- cluster ready ----"
kubectl get nodes
echo
echo "Use the cluster in another shell with:"
echo "  export KUBECONFIG=$KUBECONFIG"
