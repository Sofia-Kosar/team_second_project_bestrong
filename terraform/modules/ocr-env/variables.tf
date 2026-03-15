variable "resource_group_name" {
  description = "Name of the Resource Group for OCR resources"
  type        = string
  default     = "rg-bestrong-ocr"
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
