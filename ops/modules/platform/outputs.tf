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
  value       = length(data.aws_acm_certificate.selected) > 0 ? data.aws_acm_certificate.selected[0] : null
}

output "permissions_boundary" {
  description = "IAM permissions boundary ARN"
  value       = length(data.aws_iam_policy.permissions_boundary) > 0 ? data.aws_iam_policy.permissions_boundary[0].arn : null
}

output "sg_cmscloud_vpn" {
  description = "CMS Cloud VPN security group"
  value       = length(data.aws_security_group.cmscloud_vpn) > 0 ? data.aws_security_group.cmscloud_vpn[0] : null
}

output "sg_clb_cms_vpn" {
  description = "CMS VPN CLB security group"
  value       = length(data.aws_security_group.clb_cms_vpn) > 0 ? data.aws_security_group.clb_cms_vpn[0] : null
}

output "sg_clb_akamai" {
  description = "Akamai CLB security group"
  value       = length(data.aws_security_group.clb_akamai) > 0 ? data.aws_security_group.clb_akamai[0] : null
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


