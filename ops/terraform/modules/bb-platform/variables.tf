# Blue Button Platform Module - Variables

variable "app" {
  type        = string
  default     = "bb"
  description = "Application name (short)"
}

variable "env" {
  type        = string
  default     = null
  description = "Environment name. If null, uses terraform.workspace"
}

variable "vpc_id" {
  type        = string
  default     = null
  description = "VPC ID. If provided, skips discovery via tag:Name"
}

variable "service" {
  type        = string
  description = "Service name for this terraservice"
}

variable "root_module" {
  type        = string
  default     = ""
  description = "URL or path to the root module (for tagging)"
}

variable "ssm_hierarchy_roots" {
  type        = list(string)
  default     = ["bluebutton"]
  description = "SSM parameter hierarchy roots to load"
}

variable "vpc_name_pattern" {
  type        = string
  default     = ""
  description = "VPC name pattern for lookup. If empty, uses *{parent_env}* pattern"
}

variable "kms_key_alias" {
  type        = string
  default     = ""
  description = "KMS key alias for encryption"
}

variable "acm_domain" {
  type        = string
  default     = ""
  description = "ACM certificate domain for lookup"
}

variable "permissions_boundary_name" {
  type        = string
  default     = "ct-ado-poweruser-permissions-boundary-policy"
  description = "IAM permissions boundary policy name"
}

variable "additional_tags" {
  type        = map(string)
  default     = {}
  description = "Additional tags to merge with default tags"
}
