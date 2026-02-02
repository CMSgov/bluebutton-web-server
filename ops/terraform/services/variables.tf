variable "env" {
  type        = string
  default     = null
  description = "Environment name (e.g. test, impl, prod). If null, uses OpenTofu workspace."
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
