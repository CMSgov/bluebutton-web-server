# Bootstrap Service Variables

variable "github_repo_url" {
  description = "GitHub repository URL for CodeBuild"
  type        = string
  default     = "https://github.com/CMSgov/bluebutton-web-server"
}

variable "github_org" {
  description = "GitHub organization name"
  type        = string
  default     = "CMSgov"
}

variable "github_repo" {
  description = "GitHub repository name (without org)"
  type        = string
  default     = "bluebutton-web-server"
}

variable "iam_path" {
  description = "IAM path for roles"
  type        = string
  default     = "/"
}
