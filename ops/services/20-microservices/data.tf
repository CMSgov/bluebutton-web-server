# terraform/services/20-microservices/data.tf
# Cross-service references via AWS data sources (BFD/AB2D pattern — no remote state)

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# ============================================================================
# Cluster Reference (from 10-cluster service)
# Uses AWS data source instead of terraform_remote_state
# ============================================================================
data "aws_ecs_cluster" "main" {
  cluster_name = "${local.app_prefix}-${local.workspace}-cluster"
}

# ============================================================================
# Per-Service Configuration from SSM (single JSON parameter per service)
# SSM path: /bb/{env}/{service}/config — stores all ECS/scaling/ALB config as JSON
#
# Expected JSON structure:
# {
#   "port": 8000,
#   "cpu": 512,
#   "memory": 1024,
#   "count": 1,
#   "scaling_min": 1,
#   "scaling_max": 2,
#   "health_check_path": "/health",
#   "alb_enabled": true,
#   "autoscale_enabled": false
# }
# ============================================================================
data "aws_ssm_parameter" "service_config" {
  for_each = var.enable_ssm_config ? var.backend_services : toset([])
  name     = "/bb/${local.platform.env}/${each.key}/config"
}

locals {
  # Parse each service's JSON config from SSM (empty map when SSM disabled)
  ssm_service_configs = {
    for k, v in data.aws_ssm_parameter.service_config : k => jsondecode(nonsensitive(v.value))
  }
}

# ============================================================================
# ECR Repository Reference (from 00-bootstrap service)
# Uses AWS data source instead of terraform_remote_state
# Sandbox uses Prod repo (shared account) — ECR name uses bucket_env
# ============================================================================
data "aws_ecr_repository" "api" {
  name = "${local.app_prefix}-${local.bucket_env}-api"
}

locals {
  ecr_repository_url = data.aws_ecr_repository.api.repository_url
  ecr_repository_arn = data.aws_ecr_repository.api.arn
}

# ============================================================================
# Dynamic Secret Discovery (Secrets Manager only)
# ============================================================================

# Discover all Secrets Manager secrets under /bb2/{env}/app/
data "aws_secretsmanager_secrets" "app_secrets" {
  filter {
    name   = "name"
    values = ["/bb2/${local.platform.env}/app/"]
  }
}

# Get details for each discovered secret
data "aws_secretsmanager_secret" "app_secrets" {
  for_each = toset(data.aws_secretsmanager_secrets.app_secrets.arns)
  arn      = each.value
}

