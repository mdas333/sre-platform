#!/usr/bin/env bash
# load.sh — drive HTTP traffic against the Platform API so the SLO counters
# and Prometheus gauges move. Uses `hey` (brew install hey).
#
# Two patterns are available:
#   load.sh         — single pass: 10k requests, 50 concurrency
#   load.sh failing — inject a configurable failure rate (default 2%)
#                     by hitting a path that does not exist

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
export KUBECONFIG="${KUBECONFIG:-$PROJECT_DIR/infrastructure/cluster/kubeconfig}"

MODE="${1:-healthy}"
DURATION="${DURATION:-30}"
CONCURRENCY="${CONCURRENCY:-25}"
FAILURE_RATE_PCT="${FAILURE_RATE_PCT:-2}"
PORT="${PORT:-18080}"

command -v hey >/dev/null || { echo "hey not installed. brew install hey" >&2; exit 1; }

echo "Port-forwarding platform-api → localhost:${PORT} ..."
kubectl -n sre-platform port-forward svc/platform-api "${PORT}:80" >/tmp/load-pf.log 2>&1 &
PF=$!
trap 'kill $PF 2>/dev/null || true' EXIT
for i in 1 2 3 4 5 6 7 8; do
  curl -sf "http://127.0.0.1:${PORT}/healthz" >/dev/null && break
  sleep 1
done

echo
case "$MODE" in
  healthy)
    echo "── healthy load: GET /cluster/health for ${DURATION}s ──"
    hey -z "${DURATION}s" -c "$CONCURRENCY" "http://127.0.0.1:${PORT}/cluster/health" | tail -20
    ;;
  failing)
    echo "── mixed load: ${FAILURE_RATE_PCT}% failures for ${DURATION}s ──"
    # The failing path is a real 404 from the API — it still exercises the
    # request path but counts as a non-2xx in the error budget.
    TOTAL=$(( CONCURRENCY * 10 ))
    FAIL=$(( TOTAL * FAILURE_RATE_PCT / 100 ))
    OK=$(( TOTAL - FAIL ))
    ( hey -n "$OK"   -c "$CONCURRENCY" "http://127.0.0.1:${PORT}/cluster/health"   | tail -4 ) &
    ( hey -n "$FAIL" -c 2              "http://127.0.0.1:${PORT}/does-not-exist"   | tail -4 ) &
    wait
    ;;
  *)
    echo "usage: $0 [healthy|failing]" >&2
    exit 1
    ;;
esac

echo
echo "── Platform API /metrics (platform_ gauges) ──"
curl -sf "http://127.0.0.1:${PORT}/metrics" | grep '^platform_' | head -10 || true
