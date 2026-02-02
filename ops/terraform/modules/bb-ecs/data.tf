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
