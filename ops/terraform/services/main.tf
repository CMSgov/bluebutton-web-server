provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = module.platform.default_tags
  }
}

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
  app_config_bucket     = try(module.platform.ssm["/bluebutton/config/app_config_bucket"], "")
  static_content_bucket = try(module.platform.ssm["/bluebutton/config/static_content_bucket"], "")

  # Secrets from Secrets Manager
  secrets = [
    {
      name       = "DATABASE_URL"
      value_from = "arn:aws:secretsmanager:${module.platform.primary_region.name}:${module.platform.account_id}:secret:/bb2/${module.platform.env}/app/database_url"
    },
    {
      name       = "SECRET_KEY"
      value_from = "arn:aws:secretsmanager:${module.platform.primary_region.name}:${module.platform.account_id}:secret:/bb2/${module.platform.env}/app/secret_key"
    }
  ]
}

# ============================================================================
# SNS Topic for Alarms
# ============================================================================
resource "aws_sns_topic" "cloudwatch_alarms_topic" {
  name              = "bb-${module.platform.env}-cloudwatch-alarms"
  kms_master_key_id = "alias/aws/sns"
}
