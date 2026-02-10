# terraform/modules/bb-ecs/cloudwatch.tf

resource "aws_cloudwatch_log_group" "ecs" {
  for_each          = nonsensitive(local.service_config)
  name              = "/aws/ecs/fargate/${local.app_prefix}-${local.workspace}-${each.key}"
  retention_in_days = var.log_retention_days

  tags = { Name = "${local.app_prefix}-${local.workspace}-${each.key}-logs" }
}
