
# ============================================================================
# Platform Module (Terraservice Pattern)
# Provides: SSM config, VPC, subnets, KMS, ACM, environment detection
# ============================================================================
module "platform" {
  source = "../modules/bb-platform"

  app         = "bb"
  env         = var.env
  service     = "api"
  root_module = "https://github.com/CMSgov/bluebutton-web-server/tree/main/ops/terraform/services"

  # SSM hierarchy roots to load
  ssm_hierarchy_roots = ["bluebutton"]
}

# ============================================================================
# ECS Infrastructure (Terraservice Pattern)
# Pass entire platform object to module
# ============================================================================
module "bb_ecs" {
  source = "../modules/bb-ecs"

  # Pass platform object (Terraservice pattern)
  platform = {
    app                  = module.platform.app
    env                  = module.platform.env
    parent_env           = module.platform.parent_env
    service              = module.platform.service
    primary_region       = module.platform.primary_region
    account_id           = module.platform.account_id
    vpc_id               = module.platform.vpc_id
    private_subnet_ids   = module.platform.private_subnet_ids
    public_subnet_ids    = module.platform.public_subnet_ids
    private_subnets      = module.platform.private_subnets
    kms_alias            = module.platform.kms_alias
    acm_certificate      = module.platform.acm_certificate
    permissions_boundary = module.platform.permissions_boundary
    default_tags         = module.platform.default_tags
    ssm                  = module.platform.ssm
  }



  # Optional settings
  create_cluster        = true
  image_tag             = var.image_tag
  log_retention_days    = 30
  app_config_bucket     = module.platform.config.app_config_bucket
  static_content_bucket = module.platform.config.static_content_bucket

  # Backend services configuration - loaded from SSM via platform.config
  backend_services = {
    api = {
      name              = "api"
      port              = module.platform.config.api_port
      cpu               = module.platform.config.api_cpu
      memory            = module.platform.config.api_memory
      count             = module.platform.config.api_count
      min_capacity      = module.platform.config.api_min_capacity
      max_capacity      = module.platform.config.api_max_capacity
      alb               = true
      autoscale_enabled = true
      health_check_path = module.platform.config.api_health_check_path
    }
  }

  # ALB Security Groups - Environment-specific (VPN + Akamai)
  # All environments use the same pattern: bb-sg-{env}-clb-*
  alb_allow_all_ingress  = false
  alb_security_group_ids = [
    data.aws_security_group.cmscloud_vpn.id,
    data.aws_security_group.clb_cms_vpn.id,
    data.aws_security_group.clb_akamai.id,
  ]

  # Secrets are now auto-discovered from:
  # - SSM Parameter Store: /bb2/{env}/app/*
  # - Secrets Manager: /bb2/{env}/*
  # See bb-ecs/data.tf and bb-ecs/locals.tf for discovery logic
}

# ============================================================================
# Security Group Data Sources for ALB (Production/Sandbox only)
# ============================================================================
data "aws_security_group" "cmscloud_vpn" {
  filter {
    name   = "group-name"
    values = ["cmscloud-vpn"]
  }
  vpc_id = module.platform.vpc_id
}

data "aws_security_group" "clb_cms_vpn" {
  filter {
    name   = "group-name"
    values = ["bb-sg-${module.platform.parent_env}-clb-cms-vpn"]
  }
  vpc_id = module.platform.vpc_id
}

data "aws_security_group" "clb_akamai" {
  filter {
    name   = "group-name"
    values = ["bb-sg-${module.platform.parent_env}-clb-akamai-prod"]
  }
  vpc_id = module.platform.vpc_id
}

# ============================================================================
# SNS Topic for Alarms
# ============================================================================
resource "aws_sns_topic" "cloudwatch_alarms_topic" {
  name              = "bb-${module.platform.env}-cloudwatch-alarms"
  kms_master_key_id = "alias/aws/sns"
}

# ============================================================================
# CodeBuild (GitHub Actions Self-Hosted Runner)
# Includes: ECR, CodeBuild project, GitHub OIDC
# ============================================================================
module "codebuild" {
  source = "../modules/bb-codebuild"

  env                      = module.platform.env
  iam_path                 = try(module.platform.ssm["/bluebutton/config/iam_path"], "/")
  permissions_boundary_arn = module.platform.permissions_boundary
}
