#!/usr/bin/env bash
# build-and-load.sh — local dev helper.
#
# Builds the Platform API container image and imports it into the k3d
# cluster so the Deployment can use it without pushing to a registry.
# In CI the equivalent is: docker build → cosign sign (keyless OIDC) →
# push to ghcr.io. Locally we skip the push and use k3d's import path.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
IMAGE="${IMAGE:-ghcr.io/mdas333/sre-platform/platform-api:dev}"
CLUSTER="${CLUSTER:-sre-platform}"

echo "==> docker build $IMAGE"
docker build -t "$IMAGE" "$PROJECT_DIR/platform-api"

echo "==> k3d image import $IMAGE (cluster=$CLUSTER)"
k3d image import "$IMAGE" -c "$CLUSTER"

echo
echo "Image is now resolvable inside the cluster. Trigger a rollout with:"
echo "  kubectl -n sre-platform rollout restart deployment/platform-api"
