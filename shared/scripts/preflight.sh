#!/usr/bin/env bash
# preflight.sh — verify local tooling before cluster bootstrap.
# Prints a per-tool status line and exits non-zero if anything is missing.

set -u

missing=()

check() {
  local bin="$1"
  local hint="$2"
  if command -v "$bin" >/dev/null 2>&1; then
    local ver
    ver="$("$bin" --version 2>&1 | head -n1 | tr -d '\r' || true)"
    printf "  [ok] %-8s %s\n" "$bin" "$ver"
  else
    printf "  [missing] %-8s install hint: %s\n" "$bin" "$hint"
    missing+=("$bin")
  fi
}

echo "Preflight checks:"

check docker   "Docker Desktop — https://www.docker.com/products/docker-desktop"
check brew     "https://brew.sh"
check kubectl  "brew install kubectl"
check helm     "brew install helm"
check k3d      "brew install k3d"
check tofu     "brew install opentofu"
check vault    "brew install vault"
check cosign   "brew install cosign"
check jq       "brew install jq"

if docker info >/dev/null 2>&1; then
  echo "  [ok] docker daemon reachable"
else
  echo "  [missing] docker daemon not reachable — start Docker Desktop"
  missing+=("docker-daemon")
fi

echo

if [ "${#missing[@]}" -gt 0 ]; then
  echo "Preflight failed. Missing: ${missing[*]}"
  exit 1
fi

echo "Preflight passed."
