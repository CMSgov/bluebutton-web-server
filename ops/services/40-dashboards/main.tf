module "platform" {
  source    = "../../modules/platform"
  providers = { aws = aws, aws.secondary = aws.secondary }

  app         = local.app
  env         = local.env
  service     = local.service
  ssm_hierarchy_roots = ["bb"]
}

data "aws_ssm_parameter" "bcda_account_id" {
  name = "/bb/${local.env}/app/sensitive/bcda_account_id"
}

data "aws_secretsmanager_secret_version" "datadog_cicd_api_key" {
  secret_id = "arn:aws:secretsmanager:${var.region}:${sensitive(data.aws_ssm_parameter.bcda_account_id.value)}:secret:cdap/bb/${local.env}/datadog/cicd/api-key"
}

data "aws_secretsmanager_secret_version" "datadog_cicd_application_key" {
  secret_id = "arn:aws:secretsmanager:${var.region}:${sensitive(data.aws_ssm_parameter.bcda_account_id.value)}:secret:cdap/bb/${local.env}/datadog/cicd/application-key"
}

provider "datadog" {
  api_key = sensitive(data.aws_secretsmanager_secret_version.datadog_cicd_api_key.secret_string)
  app_key = sensitive(data.aws_secretsmanager_secret_version.datadog_cicd_application_key.secret_string)
  api_url = "https://api.ddog-gov.com"
}

locals {
  env     = terraform.workspace
  service = "dashboards"
  root_module = "https://github.com/CMSgov/bluebutton-web-server/tree/main/ops/services/${basename(abspath(path.module))}"

  default_tags = module.platform.default_tags

  create_dashboards = local.env == "prod"
}

module "datadog_dashboard" {
  source      = "github.com/CMSgov/cdap/terraform/modules/datadog_dashboard" # you can specify the commit hash here by appending ?ref=<latest-commit-hash> ; though I'd wait as we all iterate together on improvements to the modules
  app         = local.app                                                      #or just "bb"
  runbook_url = "https://thisisatest.cdap.internal.cms.gov"

  count = local.create_dashboards ? 1 : 0
}
