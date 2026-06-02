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

locals {
  env     = terraform.workspace
  service = "datadog"
  root_module = "https://github.com/CMSgov/bluebutton-web-server/tree/main/ops/services/${basename(abspath(path.module))}"

  default_tags = module.platform.default_tags

  ## Evaluates config/defaults.yml and overwrites values with those from config/${var.env}.yml for each
  ## variable/key type. Creates a hierarchy of defaults, so the modules/datadog_monitors defaults are
  ## the least prioritized, followed by config/defaults.yml, followed by the environment specific settings.

  defaults = yamldecode(file("config/defaults.yml"))
  # TODO local.workspace or should this be local.env?
  env_config = yamldecode(file("config/${local.env}.yml"))

  shadow_mode = lookup(local.env_config, "shadow_mode", local.defaults.shadow_mode)

  # map-typed keys
  monitor_config = merge(
    { for key in keys(local.defaults) : key => merge(
      lookup(local.defaults, key, {}),
      lookup(local.env_config, key, {})
      ) if can(keys(local.defaults[key])) # only process map-typed keys
    },
    { shadow_mode = local.shadow_mode }
  )

  # handles a case where the notifications are null
  _env_channels = try(local.env_config.notifications.channels, null)

  # always use the notification channels set up in the defaults, and adds those from the environment
  notify = join(" ", concat(
    local.defaults.notifications.channels,
    local._env_channels != null ? local._env_channels : []
  ))
}

module "common_datadog_monitors" {
  source = "github.com/CMSgov/cdap/terraform/modules/datadog_monitors" # you can specify the commit hash here by appending ?ref=<latest-commit-hash> ; though I'd wait as we all iterate together on improvements to the modules

  app            = local.app
  env            = local.env
  monitor_config = local.monitor_config
  notify         = local.notify
}

module "datadog_dashboard" {
  source      = "github.com/CMSgov/cdap/terraform/modules/datadog_dashboard" # you can specify the commit hash here by appending ?ref=<latest-commit-hash> ; though I'd wait as we all iterate together on improvements to the modules
  app         = local.app                                                      #or just "bb"
  runbook_url = "https://thisisatest.cdap.internal.cms.gov"
}
