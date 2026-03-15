output "function_app_name" {
  description = "Name of the OCR Azure Function App"
  value       = azurerm_linux_function_app.ocr.name
}

output "storage_account_name" {
  description = "Name of the OCR Storage Account"
  value       = azurerm_storage_account.ocr.name
}

output "file_share_name" {
  description = "Name of the File Share for PDF input"
  value       = azurerm_storage_share.pdf_input.name
}

output "blob_container_name" {
  description = "Name of the Blob container for JSON results"
  value       = azurerm_storage_container.results.name
}

output "doc_intelligence_endpoint" {
  description = "Endpoint of the Document Intelligence service"
  value       = azurerm_cognitive_account.doc_intelligence.endpoint
}

output "openai_endpoint" {
  description = "Endpoint of the Azure OpenAI service"
  value       = azurerm_cognitive_account.openai.endpoint
}

output "resource_group_name" {
  description = "Name of the OCR Resource Group"
  value       = azurerm_resource_group.ocr.name
}
