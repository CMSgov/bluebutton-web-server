# terraform/modules/bb-ecs/cloudwatch.tf

locals {
  # 1. Extract the base service keys safely
  service_keys = [for k, v in nonsensitive(local.service_config) : k]

  # 2. Map of base log groups (e.g., "serviceA" => "serviceA")
  base_log_groups = { 
    for key in local.service_keys : key => key 
  }

  # 3. Map of product log groups (e.g., "serviceA-log1" => "serviceA-log1")
  # setproduct creates the combinations, the for loop formats them into strings
  product_tuples = setproduct(local.service_keys, var.log_groups)
  extra_log_groups = { 
    for pair in local.product_tuples : "${pair[0]}-${pair[1]}" => "${pair[0]}-${pair[1]}" 
  }

  # 4. Merge both maps into one continuous collection
  all_log_groups = merge(local.base_log_groups, local.extra_log_groups)
}

resource "aws_cloudwatch_log_group" "ecs" {
  for_each = local.all_log_groups

  # each.value will output either the base service name or the combined "service-loggroup" string
  name              = "/aws/ecs/fargate/${local.app_prefix}-${local.workspace}-${each.value}"
  retention_in_days = var.log_retention_days
  kms_key_id        = local.kms_key_arn

  tags = { 
    Name = "${local.app_prefix}-${local.workspace}-${each.value}-logs" 
  }
}

resource "aws_cloudwatch_log_group" "ecs" {
  for_each          = nonsensitive(local.service_config)
  name              = "/aws/ecs/fargate/${local.app_prefix}-${local.workspace}-${each.key}"
  retention_in_days = var.log_retention_days
  kms_key_id        = local.kms_key_arn
  tags = { Name = "${local.app_prefix}-${local.workspace}-${each.key}-logs" }
}

resource "aws_cloudwatch_log_group" "ecs" {
  for_each          = setproduct(local.service_config, var.log_groups)
  name              = "/bb/${local.app_prefix}-${local.workspace}-${each.key}"
  retention_in_days = var.log_retention_days
  kms_key_id        = local.kms_key_arn
  tags = { Name = "${local.app_prefix}-${local.workspace}-${each.key}-logs" }
}