# Cluster bootstrap runbook

Ordered sequence to spin up the full Project 01 environment from a clean laptop. Shared across projects; Project 01 is the first consumer.

## Prerequisites

- macOS or Linux.
- Docker Desktop (or equivalent engine) running and reachable.
- Homebrew available for installing CLI tools.

## Sequence

1. Run the preflight script:
   ```
   ./shared/scripts/preflight.sh
   ```
   Expected: every check prints `[ok]`.

2. Change into Project 01:
   ```
   cd project-01-sre-platform
   ```

3. Bring up the cluster and platform stack:
   ```
   ./scripts/cluster-up.sh
   ```
   Expected duration: 6–10 minutes on a mid-range laptop. The script:
   - provisions the k3d cluster with OpenTofu,
   - installs Vault (dev mode),
   - installs SigNoz,
   - installs KEDA with the HTTP add-on,
   - installs ArgoCD,
   - applies the root ArgoCD Application, which syncs the Platform API.

4. Verify the Platform API:
   ```
   curl -s http://localhost:8080/cluster/health | jq
   ```

5. Open SigNoz:
   ```
   open http://localhost:3301
   ```

## Teardown

```
cd project-01-sre-platform
./scripts/cluster-down.sh
```

Runs in under a minute. Destroys the k3d cluster and reclaims all Docker resources.

## Troubleshooting

See `project-01-sre-platform/docs/setup.md` for the current list of known issues and fixes.
