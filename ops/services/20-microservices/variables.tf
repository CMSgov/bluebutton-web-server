# terraform/services/20-microservices/variables.tf

variable "backend_services" {
  type        = set(string)
  description = "Service names to configure (all values loaded from SSM)"
  default     = ["api"]
}

variable "enable_ssm_config" {
  type        = bool
  default     = true
  description = "Read service config from SSM (/bb/{env}/{service}/config). Set false to use defaults only."
}

variable "service_overrides" {
  type = map(object({
    cpu               = optional(number)
    memory            = optional(number)
    count             = optional(number)
    min_capacity      = optional(number)
    max_capacity      = optional(number)
    health_check_path = optional(string)
  }))
  default     = {}
  description = <<-EOT
    Per-service configuration overrides (bypasses SSM for testing/emergency scenarios).
    All values are optional. If not provided, SSM values are used.
    
    Example:
      service_overrides = {
        api = {
          cpu          = 1024
          memory       = 2048
          count        = 1
          min_capacity = 1
          max_capacity = 2
        }
      }
  EOT
}

variable "create_cluster" {
  type        = bool
  default     = true
  description = "Create new ECS cluster or use existing"
}

variable "cluster_name" {
  type        = string
  default     = ""
  description = "Existing cluster name (when create_cluster = false)"
}

variable "image_tag" {
  type        = string
  default     = "latest"
  description = "Container image tag"
}

variable "log_retention_days" {
  type        = number
  default     = 30
  description = "CloudWatch log retention in days"
}

variable "cpu_target_value" {
  type        = number
  default     = 70
  description = "CPU target for auto scaling"
}

variable "memory_target_value" {
  type        = number
  default     = 80
  description = "Memory target for auto scaling"
}

variable "app_config_bucket" {
  type        = string
  default     = ""
  description = "App config S3 bucket"
}

variable "static_content_bucket" {
  type        = string
  default     = ""
  description = "Static content S3 bucket"
}

variable "secrets" {
  type = list(object({
    name       = string
    value_from = string
  }))
  default     = []
  description = "Secrets to inject from Secrets Manager"
}

variable "enable_deletion_protection" {
  type        = bool
  default     = false
  description = "Enable ALB deletion protection"
}

variable "enable_access_logs" {
  type        = bool
  default     = true
  description = "Enable ALB access logs"
}

variable "access_logs_bucket" {
  type        = string
  default     = ""
  description = "S3 bucket for ALB access logs"
}

# Environment variables (migrated from env.j2 template in bluebutton-web-deployment)
# Pass additional Django settings beyond the defaults in locals.tf
variable "environment_variables" {
  type = list(object({
    name  = string
    value = string
  }))
  default     = []
  description = "Additional environment variables for Django (hostname, email, SLSx, etc.)"
}

# ALB Security Groups - Environment-specific
# These should reference existing security groups that are environment-specific:
# - cmscloud-vpn (shared across all envs)
# - bb-sg-{env}-clb-cms-vpn
# - bb-sg-{env}-clb-akamai-prod
variable "alb_security_group_ids" {
  type        = list(string)
  default     = []
  description = "Additional security group IDs to attach to ALB (VPN, Akamai, etc.)"
}

variable "alb_allow_all_ingress" {
  type        = bool
  default     = false
  description = "Allow HTTPS from 0.0.0.0/0 when true, restrict to VPN/CDN security groups when false"
}

variable "alarm_email" {
  type        = string
  default     = ""
  description = "Email address for CloudWatch alarm notifications (optional)"
}
