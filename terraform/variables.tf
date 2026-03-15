variable "resource_group_name" {
  description = "Name of the Azure Resource Group"
  type        = string
  default     = "rg-bestrong-demo"
}

variable "location" {
  description = "Azure region to deploy resources"
  type        = string
  default     = "francecentral"
}

variable "acr_name_prefix" {
  description = "Prefix for the Azure Container Registry name (must be unique globally)"
  type        = string
  default     = "acrbestrongkhrys"
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
  default     = "Standard_B2as_v2"
}

variable "ocr_resource_group_name" {
  description = "Name of the Resource Group for OCR/AI resources"
  type        = string
  default     = "rg-bestrong-ocr"
}

variable "discord_webhook_url" {
  description = "Discord incoming webhook URL for result notifications"
  type        = string
  sensitive   = true
  default     = ""
}

variable "slack_webhook_url" {
  description = "Slack incoming webhook URL for result notifications"
  type        = string
  sensitive   = true
  default     = ""
}

variable "openai_api_key" {
  description = "API key from platform.openai.com"
  type        = string
  sensitive   = true
  default     = ""
}

variable "environment" {
  description = "Deployment environment: dev or prod"
  type        = string
  default     = "dev"
}