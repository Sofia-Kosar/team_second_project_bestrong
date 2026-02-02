output "resource_group_name" {
  description = "The name of the created Resource Group"
  value       = module.bestrong_aks.resource_group_name
}

output "acr_login_server" {
  description = "The login server URL for the Azure Container Registry"
  value       = module.bestrong_aks.acr_login_server
}

output "aks_cluster_name" {
  description = "The name of the AKS Cluster"
  value       = module.bestrong_aks.aks_cluster_name
}

output "kube_config" {
  description = "Raw Kubernetes config to be used by kubectl"
  value       = module.bestrong_aks.kube_config
  sensitive   = true
}