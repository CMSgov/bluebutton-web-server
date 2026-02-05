# terraform/modules/bb-ecs/data.tf
# SSM config is passed from bb-platform via var.platform.ssm

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# ECS Cluster (if existing)
data "aws_ecs_cluster" "existing" {
  count        = var.create_cluster ? 0 : 1
  cluster_name = var.cluster_name
}

# SSM config comes from var.platform.ssm (loaded by bb-platform module)
# No need to load SSM parameters here again
locals {
  # Use the SSM config passed from platform module
  ssm_config = var.platform.ssm
}

# ============================================================================
# Dynamic Secret Discovery (Secrets Manager only)
# ============================================================================

# Discover all Secrets Manager secrets under /bb2/{env}/
data "aws_secretsmanager_secrets" "app_secrets" {
  filter {
    name   = "name"
    values = ["/bb2/${var.platform.env}/"]
  }
}

# Get details for each discovered secret
data "aws_secretsmanager_secret" "app_secrets" {
  for_each = toset(data.aws_secretsmanager_secrets.app_secrets.arns)
  arn      = each.value
}
