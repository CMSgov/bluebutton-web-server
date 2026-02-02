# terraform/modules/bb-ecs/variables.tf
# Using platform object following Terraservice pattern

variable "platform" {
  description = "Platform object from bb-platform module"
  type = object({
    app                  = string
    env                  = string
    parent_env           = string
    service              = string
    primary_region       = any
    account_id           = string
    vpc_id               = string
    private_subnet_ids   = list(string)
    public_subnet_ids    = list(string)
    private_subnets      = any
    kms_alias            = any
    acm_certificate      = any
    permissions_boundary = string
    default_tags         = map(string)
    ssm                  = map(string)
  })
}

variable "backend_services" {
  type        = map(any)
  description = "Map of backend services configuration"
  default = {
    api = {
      name              = "api"
      port              = 8000
      cpu               = 512
      memory            = 1024
      count             = 2
      min_capacity      = 1
      max_capacity      = 4
      alb               = true
      autoscale_enabled = true
      health_check_path = "/health"
    }
  }
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

# Certificate Secrets (base64-encoded in Secrets Manager)
# These match the paths from EC2 user_data.tpl:
# /bb2/${env}/app/www_key_file, /bb2/${env}/app/www_combined_crt, etc.

variable "www_key_secret_arn" {
  type        = string
  default     = ""
  description = "Secrets Manager ARN for SSL private key (base64)"
}

variable "www_cert_secret_arn" {
  type        = string
  default     = ""
  description = "Secrets Manager ARN for SSL certificate (base64)"
}

variable "fhir_cert_secret_arn" {
  type        = string
  default     = ""
  description = "Secrets Manager ARN for FHIR client certificate (base64)"
}

variable "fhir_key_secret_arn" {
  type        = string
  default     = ""
  description = "Secrets Manager ARN for FHIR client private key (base64)"
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
