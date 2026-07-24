# TODO should these go in a data file?
data "aws_ssm_parameter" "hostname_url" {
  name = "/bb/${local.env}/app/nonsensitive/hostname_url"
}

data "aws_ssm_parameter" "akamai_aca_token" {
  name = "/bb/${local.env}/app/sensitive/akamai_aca_token"
}

locals {
  hostname_url            = nonsensitive(data.aws_ssm_parameter.hostname_url.value)
  hostname_url_normalized = "%{if !startswith(local.hostname_url, "https://")}https://%{endif}${trimsuffix(local.hostname_url, "/")}"
}

module "synthetics" {
  source = "github.com/CMSgov/cdap/terraform/modules/datadog_synthetics?ref=18ff14fe868edb8a0a9dca0bedcdb0b2bfce64ce"

  app = local.app
  env = local.env

  notify               = module.common_datadog_monitors.notify
  shadow_mode          = local.monitor_config.shadow_mode
  min_failure_duration = local.monitor_config.synthetics.min_failure_duration

  tests = []
}

resource "datadog_synthetics_test" "homepage_uptime" {
  name    = "${local.app}-${local.env}-homepage-uptime"
  type    = "api"
  subtype = "http"
  status  = "live"
  message = "Synthetics test ${local.app}-${local.env}-homepage-uptime has failed. ${module.common_datadog_monitors.notify}"

  locations = module.synthetics.non_private_location_ids

  options_list {
    tick_every           = 60
    monitor_name         = "[${upper(local.env)}] [${local.app}] Synthetics — homepage-uptime"
    min_failure_duration = local.monitor_config.synthetics.min_failure_duration
  }

  tags = module.synthetics.base_tags

  # TODO should we use a global variable instead?
  dynamic "config_variable" {
    for_each = local.env == "test" ? [1] : []
    content {
      name    = "AKAMAI_COOKIE"
      type    = "text"
      secure  = true
      pattern = data.aws_ssm_parameter.akamai_aca_token.value
    }
  }

  request_headers = local.env == "test" ? {
    cookie = "{{ AKAMAI_COOKIE }}"
  } : {}

  request_definition {
    method = "GET"
    url    = local.hostname_url_normalized
  }

  assertion {
    type     = "statusCode"
    operator = "is"
    target   = "200"
  }

  assertion {
    type     = "header"
    operator = "is"
    target   = "text/html; charset=utf-8"
    property = "content-type"
  }
}

locals {
  health_endpoints = [for p in [
    "",
    "/external",
    "/external_v2",
    "/sls",
    "/db",
    "/bfd",
    "/bfd_v2",
  ] : "/health${p}"]
}

resource "datadog_synthetics_test" "health" {
  for_each = toset(local.health_endpoints)

  name    = "${local.app}-${local.env}-${each.key}"
  type    = "api"
  subtype = "http"
  status  = "live"
  message = "Synthetics test ${local.app}-${local.env}-${each.key} has failed. ${module.common_datadog_monitors.notify}"

  locations = module.synthetics.non_private_location_ids

  options_list {
    tick_every           = 60
    monitor_name         = "[${upper(local.env)}] [${local.app}] Synthetics — ${each.key}"
    min_failure_duration = local.monitor_config.synthetics.min_failure_duration
  }

  tags = module.synthetics.base_tags

  config_variable {
    name    = "AKAMAI_COOKIE"
    type    = "text"
    secure  = true
    pattern = data.aws_ssm_parameter.akamai_aca_token.value
  }

  request_headers = {
    cookie = "{{ AKAMAI_COOKIE }}"
  }

  request_definition {
    method = "GET"
    url    = "${local.hostname_url_normalized}${each.key}"
  }

  assertion {
    type     = "statusCode"
    operator = "is"
    target   = "200"
  }

  assertion {
    type     = "header"
    operator = "is"
    target   = "application/json"
    property = "content-type"
  }

  assertion {
    type     = "body"
    operator = "is"
    target   = "{\"message\":\"all's well\"}"
  }
}
