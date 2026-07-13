module "platform" {
  source    = "../../modules/platform"
  providers = { aws = aws, aws.secondary = aws.secondary }

  app                 = local.app
  env                 = local.env
  service             = local.service
  root_module = "https://github.com/CMSgov/bluebutton-web-server/tree/main/ops/services/${basename(abspath(path.module))}"
  ssm_hierarchy_roots = ["bb"]
}

data "aws_ssm_parameter" "bcda_account_id" {
  name = "/bb/${local.env}/app/sensitive/bcda_account_id"
}

data "aws_secretsmanager_secret_version" "datadog_cicd_api_key" {
  secret_id = "arn:aws:secretsmanager:${var.region}:${sensitive(data.aws_ssm_parameter.bcda_account_id.value)}:secret:/cdap/bb/${local.env}/datadog/cicd/api-key"
}

data "aws_secretsmanager_secret_version" "datadog_cicd_application_key" {
  secret_id = "arn:aws:secretsmanager:${var.region}:${sensitive(data.aws_ssm_parameter.bcda_account_id.value)}:secret:/cdap/bb/${local.env}/datadog/cicd/application-key"
}

locals {
  env         = terraform.workspace
  service     = "dashboards"

  default_tags = module.platform.default_tags

  create_dashboards = local.env == "prod"
}

module "datadog_dashboard" {
  source      = "github.com/CMSgov/cdap/terraform/modules/datadog_dashboard?ref=0aba1af484320d0d121d804c05f36cf1a4d978c9"

  app         = local.app
  runbook_url = "https://github.com/CMSgov/bluebutton-web-server/blob/master/ops/services/RUNBOOK.md"

  enable_default_widgets = {
    ecs    = true
    lambda = false
    alb    = true
    sns    = false
    sqs    = false
    aurora = true
    s3     = false
    apm    = true
  }

  widget_live_spans = {
    lambda = "2d"
    s3     = "1w"
    sqs    = "4h"
    sns    = "4h"
    ecs    = "1d"
    alb    = "1d"
    aurora = "4h"
    apm    = "1h"
  }

  apm_primary_operation = "django.request"

  count = local.create_dashboards ? 1 : 0
}
