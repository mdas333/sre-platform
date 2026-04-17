variable "cluster_name" {
  description = "k3d cluster name. Also used as the kubeconfig context name."
  type        = string
  default     = "sre-platform"
}

variable "k3d_config_path" {
  description = "Path to the k3d declarative config file."
  type        = string
  default     = "./k3d-config.yaml"
}

variable "kubeconfig_output" {
  description = "Where to write the kubeconfig extracted from the cluster."
  type        = string
  default     = "./kubeconfig"
}
