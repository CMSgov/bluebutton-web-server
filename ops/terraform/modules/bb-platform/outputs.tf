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

# Config access - all values required from SSM (no defaults)
output "config" {
  description = "Configuration values from SSM (all required)"
  value = {
    # API Service Config
    api_port              = tonumber(local.ssm_config["/bluebutton/config/api_port"])
    api_cpu               = tonumber(local.ssm_config["/bluebutton/config/api_cpu"])
    api_memory            = tonumber(local.ssm_config["/bluebutton/config/api_memory"])
    api_count             = tonumber(local.ssm_config["/bluebutton/config/api_count"])
    api_min_capacity      = tonumber(local.ssm_config["/bluebutton/config/api_min_capacity"])
    api_max_capacity      = tonumber(local.ssm_config["/bluebutton/config/api_max_capacity"])
    api_health_check_path = local.ssm_config["/bluebutton/config/api_health_check_path"]
    api_alb               = tobool(local.ssm_config["/bluebutton/config/api_alb"])
    api_autoscale_enabled = tobool(local.ssm_config["/bluebutton/config/api_autoscale_enabled"])

    # S3 Buckets (optional - used for IAM permissions)
    app_config_bucket     = try(local.ssm_config["/bluebutton/config/app_config_bucket"], "")
    static_content_bucket = try(local.ssm_config["/bluebutton/config/static_content_bucket"], "")
  }
}

