# Variables for bb-codebuild module

variable "env" {
  type        = string
  description = "Environment name (e.g., test, sandbox, prod)"
}

variable "github_repo_url" {
  type        = string
  description = "GitHub repository URL"
  default     = "https://github.com/CMSgov/bluebutton-web-server"
}

variable "github_org" {
  type        = string
  description = "GitHub organization name"
  default     = "CMSgov"
}

variable "github_repo" {
  type        = string
  description = "GitHub repository name"
  default     = "bluebutton-web-server"
}

variable "kms_key_arn" {
  type        = string
  description = "ARN of KMS key for encrypting logs (optional)"
  default     = null
}

variable "iam_path" {
  type        = string
  description = "IAM path for roles and policies"
  default     = "/"
}

variable "permissions_boundary_arn" {
  type        = string
  description = "ARN of IAM permissions boundary (optional)"
  default     = null
}
