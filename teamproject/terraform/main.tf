terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

module "bestrong_aks" {
  source = "./modules/aks-env"

  resource_group_name = var.resource_group_name
  location            = var.location
  acr_name_prefix     = var.acr_name_prefix
  aks_cluster_name    = var.aks_cluster_name
  dns_prefix          = var.dns_prefix
  node_count          = var.node_count
  vm_size             = var.vm_size
}