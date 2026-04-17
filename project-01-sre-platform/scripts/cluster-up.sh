#!/usr/bin/env bash
# cluster-up.sh — bring up the full Project 01 environment from zero.
#
# Phases:
#   1) k3d cluster (OpenTofu)
#   2) KEDA (autoscaling)
#   3) Vault dev mode + Kubernetes auth bootstrap
#   4) ArgoCD (GitOps)
#   5) SigNoz (observability backend)
#   6) OpenTelemetry Collectors (daemon + cluster singleton)
#
# Every step is idempotent. Re-running is safe.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CLUSTER_DIR="$PROJECT_DIR/infrastructure/cluster"
OBS_DIR="$PROJECT_DIR/observability"
INFRA_DIR="$PROJECT_DIR/infrastructure"

step() { echo; echo "==[ $1 ]=="; }

step "1/6  k3d cluster via OpenTofu"
cd "$CLUSTER_DIR"
tofu init -input=false -no-color
tofu apply -auto-approve -input=false -no-color
export KUBECONFIG="$CLUSTER_DIR/kubeconfig"
kubectl wait --for=condition=Ready node --all --timeout=180s

step "2/6  KEDA"
helm repo add kedacore https://kedacore.github.io/charts --force-update >/dev/null
helm upgrade --install keda kedacore/keda \
  --namespace keda --create-namespace \
  -f "$INFRA_DIR/keda/values.yaml" \
  --wait --timeout 3m

step "3/6  Vault (dev mode) + Kubernetes auth bootstrap"
helm repo add hashicorp https://helm.releases.hashicorp.com --force-update >/dev/null
helm upgrade --install vault hashicorp/vault \
  --namespace vault --create-namespace \
  -f "$INFRA_DIR/vault/values.yaml" \
  --wait --timeout 3m
kubectl wait --for=condition=Ready pod/vault-0 -n vault --timeout=120s
bash "$INFRA_DIR/vault/bootstrap.sh"

step "4/6  ArgoCD"
helm repo add argo https://argoproj.github.io/argo-helm --force-update >/dev/null
helm upgrade --install argocd argo/argo-cd \
  --namespace argocd --create-namespace \
  -f "$INFRA_DIR/argocd/values.yaml" \
  --wait --timeout 5m

step "5/6  SigNoz"
helm repo add signoz https://charts.signoz.io --force-update >/dev/null
helm upgrade --install signoz signoz/signoz \
  --namespace signoz --create-namespace \
  -f "$INFRA_DIR/signoz/values.yaml" \
  --wait --timeout 8m

step "6/6  OpenTelemetry Collectors (daemon + cluster)"
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts --force-update >/dev/null
helm upgrade --install otel-daemon open-telemetry/opentelemetry-collector \
  --namespace otel --create-namespace \
  -f "$OBS_DIR/otel-daemon-values.yaml" \
  --wait --timeout 3m
helm upgrade --install otel-cluster open-telemetry/opentelemetry-collector \
  --namespace otel \
  -f "$OBS_DIR/otel-cluster-values.yaml" \
  --wait --timeout 3m

echo
echo "====================================================================="
echo "Cluster is up."
echo
echo "Nodes:"
kubectl get nodes --no-headers
echo
echo "Open SigNoz UI:      kubectl -n signoz port-forward svc/signoz 3301:8080"
echo "Open ArgoCD UI:      kubectl -n argocd port-forward svc/argocd-server 8080:80"
echo "ArgoCD admin pwd:    kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d; echo"
echo
echo "Use the cluster in another shell:"
echo "  export KUBECONFIG=$KUBECONFIG"
echo "====================================================================="
