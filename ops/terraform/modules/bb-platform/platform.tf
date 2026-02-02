# Blue Button Platform Module

locals {
  app              = var.app
  env              = var.env != null ? var.env : terraform.workspace
  # Find established env name in workspace string, fallback to env itself, handle nulls
  found_env        = one([for x in ["test", "impl", "prod"] : x if can(regex("${x}", local.env))])
  parent_env       = local.found_env != null ? local.found_env : local.env
  sdlc_env         = contains(["impl", "prod"], coalesce(local.parent_env, "none")) ? "production" : "non-production"
  service          = var.service

  # Standard tags
  static_tags = {
    application    = local.app
    business       = "oeda"
    environment    = local.env
    parent_env     = local.parent_env
    service        = local.service
    opentofu       = true
    tf_root_module = var.root_module
  }

  # SSM hierarchies to load
  ssm_hierarchies = flatten([
    for root in var.ssm_hierarchy_roots :
    ["/${root}/${local.env}/common", "/${root}/${local.env}/config"]
  ])

  # Flatten SSM data into a map
  ssm_flattened_data = {
    names = flatten([for k, v in data.aws_ssm_parameters_by_path.params : v.names])
    values = flatten([for k, v in data.aws_ssm_parameters_by_path.params : nonsensitive(v.values)])
  }

  ssm_config = zipmap(
    [for name in local.ssm_flattened_data.names : replace(name, "/((non)*sensitive|${local.env})//", "")],
    local.ssm_flattened_data.values
  )

  # Resolved ACM Domain: 1) Variable 2) SSM 3) Default Pattern
  # Use coalesce to avoid null in string template
  resolved_acm_domain = var.acm_domain != "" ? var.acm_domain : try(local.ssm_config["/bluebutton/config/acm_domain"], "${coalesce(local.parent_env, "test")}.bluebutton.cms.gov")

  # VPC ID resolution logic: Prefer variable if provided, else use discovery
  vpc_id = var.vpc_id != null ? var.vpc_id : try(data.aws_vpc.this[0].id, "")
}

# Data Sources
data "aws_region" "primary" {}

data "aws_caller_identity" "current" {}

data "aws_ssm_parameters_by_path" "params" {
  for_each = toset(local.ssm_hierarchies)

  recursive       = true
  path            = each.value
  with_decryption = true
}

# VPC Discovery (Only runs if vpc_id not provided)
data "aws_vpc" "this" {
  count = var.vpc_id == null ? 1 : 0
  filter {
    name   = "tag:Name"
    values = var.vpc_name_pattern != "" ? [var.vpc_name_pattern] : ["*${coalesce(local.parent_env, "")}*"]
  }
}

# Subnets
data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [local.vpc_id]
  }
  filter {
    name   = "tag:Name"
    values = ["*private*"]
  }
}

data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [local.vpc_id]
  }
  filter {
    name   = "tag:Name"
    values = ["*public*"]
  }
}

data "aws_subnet" "private" {
  for_each = toset(data.aws_subnets.private.ids)
  id       = each.key
}

data "aws_subnet" "public" {
  for_each = toset(data.aws_subnets.public.ids)
  id       = each.key
}

# KMS Key
data "aws_kms_alias" "primary" {
  count = var.kms_key_alias != "" ? 1 : 0
  name  = var.kms_key_alias
}

# ACM Certificate (Automatic resolution)
data "aws_acm_certificate" "selected" {
  domain      = local.resolved_acm_domain
  statuses    = ["ISSUED"]
  most_recent = true
}

# IAM Permissions Boundary
data "aws_iam_policy" "permissions_boundary" {
  count = var.permissions_boundary_name != "" ? 1 : 0
  name  = var.permissions_boundary_name
}
