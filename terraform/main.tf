terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }

  backend "azurerm" {
    resource_group_name  = "bestrong-tfstate-rg"
    storage_account_name = "besstrongtfstate"
    container_name       = "tfstate"
    key                  = "terraform.tfstate"
  }
}

provider "azurerm" {
  features {}
  subscription_id = "3e3b714c-5258-412b-a789-22e19a55fc7c"
  tenant_id       = "349810a8-5481-4382-a268-9c7e02cc0fbd"
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

module "bestrong_ocr" {
  source = "./modules/ocr-env"

  resource_group_name = var.ocr_resource_group_name
  location            = var.location
  discord_webhook_url = var.discord_webhook_url
  slack_webhook_url   = var.slack_webhook_url
}