variable "env" {
  type        = string
  default     = null
  description = "Environment name (e.g. test, impl, prod). If null, uses OpenTofu workspace."
}

variable "region" {
  type        = string
  default     = "us-east-1"
  description = "Primary AWS region"
}

variable "secondary_region" {
  type        = string
  default     = "us-west-2"
  description = "Secondary AWS region for DR/failover"
}

variable "image_tag" {
  type        = string
  default     = "latest"
  description = "Container image tag to deploy"
}

variable "acm_domain" {
  type        = string
  default     = ""
  description = "ACM certificate domain for ALB HTTPS"
}
