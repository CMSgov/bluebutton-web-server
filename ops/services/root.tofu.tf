# This root tofu.tf is symlinked to by all per-env services. Changes to this tofu.tf apply to
# _all_ services, so be careful!

locals {
  app              = "bb"
  established_envs = ["test", "sandbox", "prod"]
  service_prefix   = "${local.app}-${local.env}"

  parent_env = coalesce(
    var.parent_env,
    try(
      one([for x in local.established_envs : x if can(regex("${x}$$", terraform.workspace))]),
      "invalid-workspace"
    ),
    "invalid-parent-env" # No default — forces explicit -var="parent_env=..." on init
  )

  # Per-environment state buckets (CMS Cloud style)
  # Sandbox and Prod share the same bucket (same account)
  bucket_env = local.parent_env == "sandbox" ? "prod" : local.parent_env

  # Shared foundation buckets
  app_config_bucket = "bb-${local.bucket_env}-app-config"
}

variable "region" {
  description = "AWS region for resources"
  default     = "us-east-1"
  nullable    = false
  type        = string
}

variable "parent_env" {
  description = <<-EOF
  The parent environment of the current solution. Will correspond with `terraform.workspace`.
  Necessary on `tofu init` and `tofu workspace select` _only_. In all other situations, parent env
  will be divined from `terraform.workspace`.
  EOF
  type        = string
  nullable    = true
  default     = null
  validation {
    # Must hardcode list here because "validation" block cannot reference "locals"
    # This checks valid input values only; bucket logic (sandbox->prod bucket) is handled in locals
    condition     = var.parent_env == null || contains(["test", "sandbox", "prod"], var.parent_env)
    error_message = "Invalid parent environment name. Must be one of: test, sandbox, prod."
  }
}

variable "root_module" {
  description = "Root module URL for tracking (e.g., GitHub URL)"
  type        = string
  nullable    = false
  default     = "https://github.com/CMSgov/bluebutton-web-server"
}

variable "secondary_region" {
  description = "Secondary AWS region for DR/failover"
  default     = "us-west-2"
  nullable    = false
  type        = string
}

provider "aws" {
  region = var.region
  default_tags {
    tags = local.default_tags
  }
}

provider "aws" {
  alias  = "secondary"
  region = var.secondary_region
  default_tags {
    tags = local.default_tags
  }
}

terraform {
  backend "s3" {
    # Dynamic backend configuration
    # OpenTofu 1.8+ allows using locals and variables here
    bucket  = "bb-${local.bucket_env}-app-config"
    key     = "ops/services/${local.service}/tofu.tfstate"
    region  = var.region
    encrypt = true
    use_lockfile = true
    # TODO: Enable after creating KMS key alias/bb-{env}-cmk in 00-bootstrap
    # kms_key_id = "alias/bb-${local.bucket_env}-cmk"
  }

  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6"
    }
  }
}
