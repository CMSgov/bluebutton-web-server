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
  service     = "monitors"

  default_tags = module.platform.default_tags

  ## Evaluates config/defaults.yml and overwrites values with those from config/${local.env}.yml for each
  ## variable/key type. Creates a hierarchy of defaults, so the modules/datadog_monitors defaults are
  ## the least prioritized, followed by config/defaults.yml, followed by the environment specific settings.

  defaults   = yamldecode(file("config/defaults.yml"))
  env_config = yamldecode(file("config/${local.env}.yml"))

  monitor_config = {
    for key in distinct(concat(keys(local.defaults), keys(local.env_config))) :
    key => try(
      # Attempt map merge (works if both values are map/object-typed)
      merge(
        lookup(local.defaults, key, {}),
        lookup(local.env_config, key, {})
      ),
      # Fallback to scalar: env wins, then default
      lookup(local.env_config, key, lookup(local.defaults, key, null))
    )
  }
}

module "common_datadog_monitors" {
  source = "github.com/CMSgov/cdap/terraform/modules/datadog_monitors?ref=6ded520857376f46bb317dca898e5df6a9ecc93b"

  app             = local.app
  env             = local.env
  monitor_config  = local.monitor_config
  custom_monitors = local.custom_monitors
}

locals {
  custom_monitors = [
    {
      name    = "[${upper(local.env)}] [${local.app}] ALB — Target Response Time High"
      type    = "metric alert"
      message = "ALB target has high average response time."
      query   = "avg(last_1h):avg:aws.applicationelb.target_response_time.average{application:${local.app}, environment:${local.env}} > 0.35"

      thresholds = {
        critical = 0.35
        warning  = 0.25
      }

      notify_no_data           = local.env != "test"
      no_data_timeframe_minute = 60

      # TODO the CDAP module doesn't actually do anything with this, open a PR
      require_full_window = false
    },
  ]
}
