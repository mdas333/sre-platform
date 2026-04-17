locals {
  config_sha = filesha256(var.k3d_config_path)
}

# Cluster lifecycle, driven by the k3d declarative config.
# Triggers include the config file's hash so a config change causes a
# `tofu apply` to tear down and recreate the cluster deterministically.
resource "null_resource" "k3d_cluster" {
  triggers = {
    cluster_name = var.cluster_name
    config_sha   = local.config_sha
  }

  provisioner "local-exec" {
    when    = create
    command = <<-EOT
      set -e
      if k3d cluster list --output json | jq -er '.[] | select(.name == "${var.cluster_name}")' > /dev/null 2>&1; then
        echo "cluster ${var.cluster_name} already exists; skipping create"
      else
        k3d cluster create --config ${var.k3d_config_path}
      fi
    EOT
  }

  provisioner "local-exec" {
    when    = destroy
    command = "k3d cluster delete ${self.triggers.cluster_name} || true"
  }
}

# Export the kubeconfig to a local file so downstream tooling (scripts, CI)
# can reference a stable path rather than the shared ~/.kube/config.
resource "null_resource" "kubeconfig" {
  depends_on = [null_resource.k3d_cluster]

  triggers = {
    cluster_id      = null_resource.k3d_cluster.id
    kubeconfig_path = var.kubeconfig_output
  }

  provisioner "local-exec" {
    command = "k3d kubeconfig get ${var.cluster_name} > ${var.kubeconfig_output}"
  }

  provisioner "local-exec" {
    when       = destroy
    command    = "rm -f ${self.triggers.kubeconfig_path}"
    on_failure = continue
  }
}
