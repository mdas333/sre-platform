#!/usr/bin/env bash
# verify-image.sh — verify a Platform API image was built by this repo's CI.
#
# The CI pipeline signs images with Sigstore keyless cosign using GitHub
# OIDC. Any image whose signature chains back to a workflow run in
# mdas333/sre-platform on the main branch will verify; anything else
# fails even if it shares the image tag.

set -euo pipefail

IMAGE="${1:-ghcr.io/mdas333/sre-platform/platform-api:main}"

if ! command -v cosign >/dev/null 2>&1; then
  echo "cosign not installed — brew install cosign" >&2
  exit 1
fi

cosign verify \
  --certificate-identity-regexp '^https://github\.com/mdas333/sre-platform/\.github/workflows/ci\.yml@refs/heads/.*' \
  --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
  "$IMAGE"
