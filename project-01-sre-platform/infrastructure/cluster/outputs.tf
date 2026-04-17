output "cluster_name" {
  value       = var.cluster_name
  description = "k3d cluster name"
}

output "kubeconfig_path" {
  value       = abspath(var.kubeconfig_output)
  description = "Absolute path to the cluster kubeconfig"
}

output "kubectl_context" {
  value       = "k3d-${var.cluster_name}"
  description = "kubectl context name for this cluster"
}

output "loadbalancer_endpoints" {
  value = {
    ingress   = "http://localhost:8080"
    signoz_ui = "http://localhost:3301"
    argocd_ui = "https://localhost:8233"
  }
  description = "Host-side endpoints mapped to the k3d load balancer"
}
