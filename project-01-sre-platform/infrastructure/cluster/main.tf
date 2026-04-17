locals {
  config_sha = filesha256(var.k3d_config_path)
}

# Cluster lifecycle, driven by the k3d declarative config.
# Triggers include the config file's hash so a config change causes a
# `tofu apply` to tear down and recreate the cluster deterministically.
#
# All interpolated variables are passed via `environment` and then quoted
# inside the shell script so the interpolation cannot inject arbitrary
# shell. Belt and braces: default values are safe, but treat every variable
# as untrusted input.
resource "null_resource" "k3d_cluster" {
  triggers = {
    cluster_name = var.cluster_name
    config_sha   = local.config_sha
  }

  provisioner "local-exec" {
    when    = create
    interpreter = ["/bin/bash", "-c"]
    environment = {
      CLUSTER_NAME    = var.cluster_name
      K3D_CONFIG_PATH = var.k3d_config_path
    }
    command = <<-EOT
      set -euo pipefail
      if k3d cluster list --output json | jq -er --arg name "$CLUSTER_NAME" '.[] | select(.name == $name)' > /dev/null 2>&1; then
        echo "cluster $CLUSTER_NAME already exists; skipping create"
      else
        k3d cluster create --config "$K3D_CONFIG_PATH"
      fi
    EOT
  }

  provisioner "local-exec" {
    when        = destroy
    interpreter = ["/bin/bash", "-c"]
    environment = {
      CLUSTER_NAME = self.triggers.cluster_name
    }
    command = "k3d cluster delete \"$CLUSTER_NAME\" || true"
  }
}

# Export the kubeconfig to a local file so downstream tooling (scripts, CI)
# can reference a stable path rather than the shared ~/.kube/config.
resource "null_resource" "kubeconfig" {
  depends_on = [null_resource.k3d_cluster]

  triggers = {
    cluster_id      = null_resource.k3d_cluster.id
    cluster_name    = var.cluster_name
    kubeconfig_path = var.kubeconfig_output
  }

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]
    environment = {
      CLUSTER_NAME    = var.cluster_name
      KUBECONFIG_PATH = var.kubeconfig_output
    }
    command = <<-EOT
      set -euo pipefail
      mkdir -p "$(dirname "$KUBECONFIG_PATH")"
      k3d kubeconfig get "$CLUSTER_NAME" > "$KUBECONFIG_PATH"
    EOT
  }

  provisioner "local-exec" {
    when        = destroy
    interpreter = ["/bin/bash", "-c"]
    environment = {
      KUBECONFIG_PATH = self.triggers.kubeconfig_path
    }
    command    = "rm -f \"$KUBECONFIG_PATH\""
    on_failure = continue
  }
}
