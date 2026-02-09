# ============================================================================
# Platform Module
# ============================================================================
module "platform" {
  source    = "../../modules/platform"
  providers = { aws = aws, aws.secondary = aws.secondary }

  app         = local.app
  env         = local.env
  service     = local.service
  root_module = "https://github.com/CMSgov/bluebutton-web-server/tree/main/ops/services/10-cluster"

  # SSM hierarchy roots to load
  ssm_hierarchy_roots = ["bb"]
}

locals {
  env     = terraform.workspace
  service = "cluster"

  # Platform outputs
  vpc_id             = module.platform.vpc_id
  private_subnet_ids = module.platform.private_subnet_ids
  account_id         = module.platform.account_id
}

# ============================================================================
# CloudWatch Log Group for ECS Exec
# ============================================================================
resource "aws_cloudwatch_log_group" "cluster" {
  name              = "/aws/ecs/${local.service}"
  retention_in_days = 30

  tags = {
    Name        = "bb-${local.env}-cluster-logs"
    Environment = local.env
  }
}

# ============================================================================
# ECS Cluster
# NOTE: KMS encryption disabled due to SCP/org-level restrictions
# TODO: Re-enable once KMS permissions are resolved
# ============================================================================
resource "aws_ecs_cluster" "main" {
  name = "bb-${local.env}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  configuration {
    execute_command_configuration {
      logging = "OVERRIDE"

      log_configuration {
        cloud_watch_log_group_name = aws_cloudwatch_log_group.cluster.name
      }
    }
  }

  tags = {
    Name        = "bb-${local.env}-cluster"
    Environment = local.env
  }
}

resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name

  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = "FARGATE"
  }

  default_capacity_provider_strategy {
    base              = 0
    weight            = 0
    capacity_provider = "FARGATE_SPOT"
  }
}
