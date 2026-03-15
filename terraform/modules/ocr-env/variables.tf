variable "resource_group_name" {
  description = "Name of the Resource Group for OCR resources"
  type        = string
  default     = "rg-bestrong-ocr"
}

variable "environment" {
  description = "Deployment environment: dev or prod"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "environment must be 'dev' or 'prod'."
  }
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "francecentral"
}

variable "discord_webhook_url" {
  description = "Discord incoming webhook URL"
  type        = string
  sensitive   = true
  default     = ""
}

variable "slack_webhook_url" {
  description = "Slack incoming webhook URL"
  type        = string
  sensitive   = true
  default     = ""
}

variable "create_openai_deployment" {
  description = "Set to true only when the subscription has approved OpenAI quota"
  type        = bool
  default     = false
}

variable "openai_api_key" {
  description = "API key from platform.openai.com (used instead of Azure OpenAI)"
  type        = string
  sensitive   = true
  default     = ""
}
