#!/usr/bin/env bash
# cluster-down.sh — destroy the Project 01 environment.
#
# Runs `tofu destroy` so the OpenTofu state stays consistent.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CLUSTER_DIR="$PROJECT_DIR/infrastructure/cluster"

cd "$CLUSTER_DIR"
tofu destroy -auto-approve -input=false -no-color

echo
echo "Cluster destroyed."
