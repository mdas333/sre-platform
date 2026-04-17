# Recorded demos

Two short screencaps capturing the two layers of scaling. Terminal output
recorded with `asciinema`, rendered to GIF with `agg`. Re-record after any
change that affects the output by re-running the commands in this file.

## Cluster-level scale up/down

![cluster scale](./cluster-scale.gif)

What it shows:

1. `kubectl get nodes` before — four nodes (one server, three agents).
2. `scripts/scale-cluster-up.sh` creates an additional agent (`k3d-extra-0`) and the node reaches Ready.
3. `scripts/scale-cluster-down.sh` cordons and drains the extra node, then deletes it from both k3d and the Kubernetes API.
4. `kubectl get nodes` after — back to the original four.

Repro:

```bash
asciinema rec docs/demos/cluster-scale.cast \
  --command scripts/scale-cluster-up.sh  # then ...-down.sh
agg docs/demos/cluster-scale.cast docs/demos/cluster-scale.gif --theme monokai
```

## Workload scale-to-zero (KEDA on `demo-app`)

![keda scale](./keda-scale.gif)

What it shows:

1. Initial state — `demo-app` is at zero replicas; its `ScaledObject` is `READY=True ACTIVE=False` because the cron window (08:00–09:00 UTC) is inactive.
2. The ScaledObject is patched so its cron window starts in the current minute.
3. KEDA polls at 15 s intervals and scales the deployment to the trigger's `desiredReplicas=2`. In the recording, both pods reach `Ready` within ~18 s of the patch.
4. The daily window is restored; after `cooldownPeriod: 60s` with no active trigger, KEDA returns `demo-app` to zero replicas.

The Platform API itself is never scaled to zero — it stays always-on via `k8s/platform-api/hpa.yaml` (`minReplicas: 2`). Scale-to-zero is a tenant-workload pattern, not a control-plane pattern.

Repro:

```bash
# Start from demo-app at 0:
kubectl -n sre-platform scale deployment demo-app --replicas=0
# Run the trigger script under asciinema:
asciinema rec docs/demos/keda-scale.cast \
  --command scripts/demo-keda-trigger.sh
agg docs/demos/keda-scale.cast docs/demos/keda-scale.gif --theme monokai
```
