# terraform/modules/bb-ecs/cloudwatch.tf

resource "aws_cloudwatch_log_group" "ecs" {
  for_each          = nonsensitive(local.service_config)
  name              = "/aws/ecs/fargate/${local.app_prefix}-${local.workspace}-${each.key}"
  retention_in_days = var.log_retention_days
  kms_key_id        = local.kms_key_arn
  tags = { Name = "${local.app_prefix}-${local.workspace}-${each.key}-logs" }
}

# TODO: BB2-4592 there are logs that already exist with these names in test/sbx/prod, they'll need to be added to Tofu
# resource "aws_cloudwatch_log_group" "ecs" {
#   for_each          = setproduct(local.service_config, var.log_groups)
#   name              = "/bb/${local.workspace}/app/${each.key}"
#   retention_in_days = var.log_retention_days
#   kms_key_id        = local.kms_key_arn
#   tags = { Name = "${local.app_prefix}-${local.workspace}-${each.key}-logs" }
# }