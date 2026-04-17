#!/usr/bin/env bash
# scale-cluster-down.sh — drain and remove the extra agent node.
#
# Demonstrates the opposite of scale-cluster-up: graceful eviction of workloads
# followed by node removal. Proper drain + delete, not a hard kill.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
export KUBECONFIG="$PROJECT_DIR/infrastructure/cluster/kubeconfig"

CLUSTER_NAME="${CLUSTER_NAME:-sre-platform}"
NODE_SUFFIX="${NODE_SUFFIX:-extra}"
# k3d names additional agent nodes as 'k3d-<suffix>-0' (cluster name is
# implied by the --cluster flag at create time).
KUBE_NODE="k3d-${NODE_SUFFIX}-0"

echo "---- nodes before ----"
kubectl get nodes

if ! kubectl get node "${KUBE_NODE}" >/dev/null 2>&1; then
  echo
  echo "Node ${KUBE_NODE} not found — nothing to do."
  exit 0
fi

echo
echo "Cordoning and draining ${KUBE_NODE}..."
kubectl cordon "${KUBE_NODE}"
kubectl drain "${KUBE_NODE}" \
  --ignore-daemonsets \
  --delete-emptydir-data \
  --force \
  --timeout=90s

echo
echo "Deleting ${KUBE_NODE} container from k3d runtime..."
k3d node delete "${KUBE_NODE}" || true

echo
echo "Removing stale node object from Kubernetes API..."
kubectl delete node "${KUBE_NODE}" --ignore-not-found

echo
echo "---- nodes after ----"
kubectl get nodes
