# Blue Button Platform Module - Outputs
# Following Terraservice pattern - all outputs available as module.platform.*

output "app" {
  description = "Application name"
  value       = local.app
}

output "env" {
  description = "Environment name"
  value       = local.env
}

output "parent_env" {
  description = "Parent environment (test, sandbox, prod)"
  value       = local.parent_env
}

output "sdlc_env" {
  description = "SDLC environment (production/non-production)"
  value       = local.sdlc_env
}

output "service" {
  description = "Service name"
  value       = local.service
}

output "primary_region" {
  description = "Primary AWS region"
  value       = data.aws_region.primary
}

output "account_id" {
  description = "AWS account ID"
  sensitive   = true
  value       = data.aws_caller_identity.current.account_id
}

output "secondary_region" {
  description = "Secondary AWS region for DR/failover"
  value       = var.secondary_region
}

output "aws_caller_identity" {
  description = "AWS caller identity"
  sensitive   = true
  value       = data.aws_caller_identity.current
}

output "vpc_id" {
  description = "The current environment VPC ID value"
  sensitive   = true
  value       = local.vpc_id
}

output "vpc" {
  description = "VPC data source"
  value       = length(data.aws_vpc.this) > 0 ? data.aws_vpc.this[0] : null
}

output "private_subnets" {
  description = "Private subnets map (keyed by subnet ID)"
  value       = data.aws_subnet.private
}

output "public_subnets" {
  description = "Public subnets map (keyed by subnet ID)"
  value       = data.aws_subnet.public
}

output "private_subnet_ids" {
  description = "Private subnet IDs list"
  value       = data.aws_subnets.private.ids
}

output "public_subnet_ids" {
  description = "Public subnet IDs list"
  value       = data.aws_subnets.public.ids
}

output "kms_alias" {
  description = "KMS key alias"
  value       = length(data.aws_kms_alias.primary) > 0 ? data.aws_kms_alias.primary[0] : null
}

output "kms_key_arn" {
  description = "KMS key ARN"
  value       = length(data.aws_kms_alias.primary) > 0 ? data.aws_kms_alias.primary[0].target_key_arn : null
}

output "acm_certificate" {
  description = "ACM certificate"
  value       = data.aws_acm_certificate.selected
}

output "permissions_boundary" {
  description = "IAM permissions boundary ARN"
  value       = length(data.aws_iam_policy.permissions_boundary) > 0 ? data.aws_iam_policy.permissions_boundary[0].arn : null
}

output "default_tags" {
  description = "Default tags for all resources"
  value       = merge(var.additional_tags, local.static_tags)
}

output "ssm" {
  description = "SSM configuration map"
  sensitive   = true
  value       = local.ssm_config
}

# Legacy config access - values from /bluebutton/ SSM hierarchy
# Only used by ops_old module pattern. New services read SSM directly in locals.tf.
# All values wrapped in try() since new services use "bb" hierarchy root, not "bluebutton".
output "config" {
  description = "Configuration values from SSM (legacy /bluebutton/ paths, optional)"
  value = {
    # API Service Config (optional — may not exist if using "bb" SSM root)
    api_port              = try(tonumber(local.ssm_config["/bluebutton/config/api_port"]), null)
    api_cpu               = try(tonumber(local.ssm_config["/bluebutton/config/api_cpu"]), null)
    api_memory            = try(tonumber(local.ssm_config["/bluebutton/config/api_memory"]), null)
    api_count             = try(tonumber(local.ssm_config["/bluebutton/config/api_count"]), null)
    api_min_capacity      = try(tonumber(local.ssm_config["/bluebutton/config/api_min_capacity"]), null)
    api_max_capacity      = try(tonumber(local.ssm_config["/bluebutton/config/api_max_capacity"]), null)
    api_health_check_path = try(local.ssm_config["/bluebutton/config/api_health_check_path"], null)
    api_alb               = try(tobool(local.ssm_config["/bluebutton/config/api_alb"]), null)
    api_autoscale_enabled = try(tobool(local.ssm_config["/bluebutton/config/api_autoscale_enabled"]), null)

    # S3 Buckets (SSM preferred, fallback to naming convention)
    app_config_bucket = try(
      local.ssm_config["/bluebutton/config/app_config_bucket"],
      "bb-${local.env == "sandbox" ? "prod" : local.env}-app-config"
    )
    static_content_bucket = try(
      local.ssm_config["/bluebutton/config/static_content_bucket"],
      "bb-${local.env == "sandbox" ? "prod" : local.env}-static-content"
    )
  }
}

