# Variables for bb-codebuild module

variable "env" {
  type        = string
  description = "Environment name (e.g., test, impl, prod)"
}

variable "github_repo_url" {
  type        = string
  description = "GitHub repository URL"
  default     = "https://github.com/CMSgov/bluebutton-web-server"
}

variable "buildspec_path" {
  type        = string
  description = "Path to buildspec.yml in the repository"
  default     = "buildspec.yml"
}

variable "ecr_repository_arn" {
  type        = string
  description = "ARN of ECR repository for docker push"
}

variable "ecr_repository_url" {
  type        = string
  description = "URL of ECR repository for docker push"
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
