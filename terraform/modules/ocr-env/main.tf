terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

resource "azurerm_resource_group" "ocr" {
  name     = var.resource_group_name
  location = var.location
}

# ── Storage Account ────────────────────────────────────────────────────────────

resource "azurerm_storage_account" "ocr" {
  name                     = "stbesstrongocr"
  resource_group_name      = azurerm_resource_group.ocr.name
  location                 = azurerm_resource_group.ocr.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_storage_share" "pdf_input" {
  name               = "pdf-input"
  storage_account_id = azurerm_storage_account.ocr.id
  quota              = 50
}

resource "azurerm_storage_container" "results" {
  name                  = "results"
  storage_account_id    = azurerm_storage_account.ocr.id
  container_access_type = "private"
}

# ── Azure AI Document Intelligence ────────────────────────────────────────────

resource "azurerm_cognitive_account" "doc_intelligence" {
  name                = "cog-docint-bestrong"
  location            = azurerm_resource_group.ocr.location
  resource_group_name = azurerm_resource_group.ocr.name
  kind                = "FormRecognizer"
  sku_name            = "S0"
}

# ── Azure OpenAI ───────────────────────────────────────────────────────────────

resource "azurerm_cognitive_account" "openai" {
  name                = "cog-openai-bestrong"
  location            = azurerm_resource_group.ocr.location
  resource_group_name = azurerm_resource_group.ocr.name
  kind                = "OpenAI"
  sku_name            = "S0"
}

resource "azurerm_cognitive_deployment" "gpt4o" {
  count                = var.create_openai_deployment ? 1 : 0
  name                 = "gpt-4o-mini"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "gpt-4o-mini"
    version = "2024-07-18"
  }

  sku {
    name     = "GlobalStandard"
    capacity = 1
  }
}

# ── Azure Function App ─────────────────────────────────────────────────────────

resource "azurerm_service_plan" "function" {
  name                = "plan-ocr-bestrong"
  resource_group_name = azurerm_resource_group.ocr.name
  location            = azurerm_resource_group.ocr.location
  os_type             = "Linux"
  sku_name            = "Y1"
}

resource "azurerm_linux_function_app" "ocr" {
  name                       = "func-ocr-bestrong"
  resource_group_name        = azurerm_resource_group.ocr.name
  location                   = azurerm_resource_group.ocr.location
  storage_account_name       = azurerm_storage_account.ocr.name
  storage_account_access_key = azurerm_storage_account.ocr.primary_access_key
  service_plan_id            = azurerm_service_plan.function.id

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME"  = "python"
    "AzureWebJobsStorage"       = azurerm_storage_account.ocr.primary_connection_string
    "STORAGE_CONNECTION_STRING" = azurerm_storage_account.ocr.primary_connection_string
    "FILE_SHARE_NAME"           = azurerm_storage_share.pdf_input.name
    "BLOB_CONTAINER_NAME"       = azurerm_storage_container.results.name
    "DOC_INTELLIGENCE_ENDPOINT" = azurerm_cognitive_account.doc_intelligence.endpoint
    "DOC_INTELLIGENCE_KEY"      = azurerm_cognitive_account.doc_intelligence.primary_access_key
    "OPENAI_ENDPOINT"           = azurerm_cognitive_account.openai.endpoint
    "OPENAI_KEY"                = azurerm_cognitive_account.openai.primary_access_key
    "OPENAI_DEPLOYMENT_NAME"    = var.create_openai_deployment ? "gpt-4o-mini" : ""
    "STORAGE_ACCOUNT_NAME"      = azurerm_storage_account.ocr.name
    "DISCORD_WEBHOOK_URL"       = var.discord_webhook_url
    "SLACK_WEBHOOK_URL"         = var.slack_webhook_url
  }
}
