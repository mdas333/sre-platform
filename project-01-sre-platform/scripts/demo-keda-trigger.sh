#!/usr/bin/env bash
# demo-keda-trigger.sh — briefly rewrite the KEDA ScaledObject so its cron
# window falls in the next two minutes, giving a visible scale-from-zero
# effect in the demo. Restores the daily window afterwards.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
export KUBECONFIG="${KUBECONFIG:-$PROJECT_DIR/infrastructure/cluster/kubeconfig}"

NS=sre-platform
SO=demo-app

START_MIN=$(date -u -v+1M +%M)
END_MIN=$(date -u -v+3M +%M)
START_HOUR=$(date -u -v+1M +%H)
END_HOUR=$(date -u -v+3M +%H)

echo "Rewriting ScaledObject $SO cron window to start=${START_MIN} ${START_HOUR}:00 → end=${END_MIN} ${END_HOUR}:00 UTC"

kubectl -n "$NS" patch scaledobject "$SO" --type=merge -p "$(cat <<EOF
{"spec":{"triggers":[{"type":"cron","metadata":{"timezone":"UTC","start":"${START_MIN} ${START_HOUR} * * *","end":"${END_MIN} ${END_HOUR} * * *","desiredReplicas":"2"}}]}}
EOF
)"

echo
echo "Watching demo-app pods for the next ~4 minutes (Ctrl-C to exit):"
kubectl -n "$NS" get pods -l app.kubernetes.io/name=demo-app -w --request-timeout=240s || true

echo
echo "Restoring daily 08:00-09:00 UTC window..."
kubectl -n "$NS" patch scaledobject "$SO" --type=merge -p \
  '{"spec":{"triggers":[{"type":"cron","metadata":{"timezone":"UTC","start":"0 8 * * *","end":"0 9 * * *","desiredReplicas":"2"}}]}}'

echo "Done."
