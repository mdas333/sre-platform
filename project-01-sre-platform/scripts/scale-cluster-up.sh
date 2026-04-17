#!/usr/bin/env bash
# scale-cluster-up.sh — add an agent node to the running cluster.
#
# Demonstrates cluster-level scaling: a live cluster gets a new agent without
# touching any existing workloads.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
export KUBECONFIG="$PROJECT_DIR/infrastructure/cluster/kubeconfig"

CLUSTER_NAME="${CLUSTER_NAME:-sre-platform}"
NODE_SUFFIX="${NODE_SUFFIX:-extra}"

echo "---- nodes before ----"
kubectl get nodes

echo
echo "Adding agent node '${NODE_SUFFIX}' to cluster '${CLUSTER_NAME}'..."
k3d node create "${NODE_SUFFIX}" --cluster "${CLUSTER_NAME}" --role agent --wait

echo
echo "---- nodes after ----"
kubectl get nodes
