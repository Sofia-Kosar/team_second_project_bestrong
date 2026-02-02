variable "resource_group_name" {
  description = "Name of the Azure Resource Group"
  type        = string
  default     = "rg-bestrong-demo"
}

variable "location" {
  description = "Azure region to deploy resources"
  type        = string
  default     = "southafricanorth"
}

variable "acr_name_prefix" {
  description = "Prefix for the Azure Container Registry name (must be unique globally)"
  type        = string
  default     = "acrbestrong01"
}

variable "aks_cluster_name" {
  description = "Name of the AKS Cluster"
  type        = string
  default     = "aks-bestrong-demo"
}

variable "dns_prefix" {
  description = "DNS prefix for the AKS cluster"
  type        = string
  default     = "bestrong-k8s"
}

variable "node_count" {
  description = "The number of nodes in the default node pool"
  type        = number
  default     = 2
}

variable "vm_size" {
  description = "The size of the Virtual Machine for the nodes"
  type        = string
  default     = "Standard_D2_v2"
}