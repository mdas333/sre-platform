terraform {
  required_version = ">= 1.8.0"

  # Intentionally no cluster provider here. k3d is a local development tool;
  # a production cluster would use aws/eks, google/gke, or azure/aks providers.
  # The cluster lifecycle is driven by k3d's own declarative YAML
  # (k3d-config.yaml) and a thin null_resource wrapper so that `tofu plan`,
  # `tofu apply`, and `tofu destroy` control lifecycle idiomatically.
  #
  # See shared/adr/0002-k3d-over-kind.md for the rationale on k3d, and
  # shared/adr/0003-opentofu-over-terraform.md for the choice of OpenTofu.
  required_providers {
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }
}
