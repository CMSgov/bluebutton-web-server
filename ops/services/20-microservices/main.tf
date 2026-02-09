

# ============================================================================
# Platform Module (CMS Cloud Terraservice Pattern)
# Provides: SSM config, VPC, subnets, KMS, ACM,environment detection
# ============================================================================
module "platform" {
  source    = "../../modules/platform"
  providers = { aws = aws, aws.secondary = aws.secondary }

  app           = local.app
  env           = local.env
  service       = local.service
  root_module   = "https://github.com/CMSgov/bluebutton-web-server/tree/main/ops/services/20-microservices"
  kms_key_alias = "alias/bb-${local.env}-app-key-alias"

  # SSM hierarchy roots to load
  ssm_hierarchy_roots = ["bb"]
}

locals {
  env = terraform.workspace

  # Terraservice-style SSM root mapping for Microservices service
  ssm_root_map = {
    microservices = "/bb/${local.env}/microservices/"
    common        = "/bb/${local.env}/common/"
    config        = "/bb/${local.env}/config/"
    core          = "/bb/${local.env}/core/"
  }

  # Reference common infrastructure from data sources
  # In standard pattern, services don't re-declare platform resources
  # Instead, they load via AWS data sources (BFD/AB2D pattern)
}

# ============================================================================
# Data Sources for Cross-Service References (CMS Cloud Pattern)
# ============================================================================

# ============================================================================
# ECS Infrastructure (Terraservice Pattern)
# Pass entire platform object to module
# ============================================================================
# ============================================================================
# ECS Infrastructure (Inline Pattern)
# Resources are defined in adjacent .tf files (ecs.tf, alb.tf, etc.)
# ============================================================================

locals {
  # Map platform module outputs to local variables expected by inline resources
  # This mimics the "platform" object that was passed to the module
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
    kms_key_arn          = module.platform.kms_key_arn
    acm_certificate      = module.platform.acm_certificate
    permissions_boundary = module.platform.permissions_boundary
    default_tags         = module.platform.default_tags
    ssm                  = module.platform.ssm
    app_config_bucket    = local.app_config_bucket

  }
}

# ============================================================================
# Security Group Data Sources for ALB
# Following standard pattern: data sources for existing resources
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
