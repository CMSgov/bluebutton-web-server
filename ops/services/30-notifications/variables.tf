# terraform/services/30-notifications/variables.tf

variable "backend_services" {
  type        = set(string)
  description = "Service names to configure notifications for (must match 20-microservices backend_services)"
  default     = ["api"]
}

variable "splunk_oncall_https_url" {
  type        = string
  default     = ""
  sensitive   = true
  description = "Splunk On-Call HTTPS routing URL for CloudWatch alarm notifications. When non-empty, creates HTTPS subscriptions on per-service SNS alarm topics."
}

variable "splunk_oncall_email" {
  type        = string
  default     = ""
  description = "Splunk On-Call email routing address for CloudWatch alarm notifications. When non-empty, creates email subscriptions on per-service SNS alarm topics."
}
