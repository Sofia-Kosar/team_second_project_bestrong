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

output "ocr_function_app_name" {
  description = "Name of the OCR Azure Function App"
  value       = module.bestrong_ocr.function_app_name
}

output "ocr_storage_account_name" {
  description = "Name of the OCR Storage Account"
  value       = module.bestrong_ocr.storage_account_name
}

output "ocr_blob_container_name" {
  description = "Name of the Blob container for JSON results"
  value       = module.bestrong_ocr.blob_container_name
}