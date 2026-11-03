locals {
  min_failure_duration_for_on_call = "last_15m"
}

resource "datadog_monitor" "on_call_health" {
  for_each = local.env == "test" ? {} : datadog_synthetics_test.health

  name    = "[${upper(local.env)}] [${local.app}] On Call — Synthetics ${each.key}"
  type    = "query alert"
  message = <<-EOT
  Synthetics test ${each.value.name} has failed over the ${local.min_failure_duration_for_on_call}.

  ${module.common_datadog_monitors.notify}
  ${module.common_datadog_monitors.victorops_notify}
  EOT

  query = <<-EOT
  sum(${local.min_failure_duration_for_on_call}):sum:synthetics.test_runs{status:failure, check_id:${each.value.id}}.as_count() / sum:synthetics.test_runs{check_id:${each.value.id}}.as_count() >= 1
  EOT

  monitor_thresholds {
    critical = 1
    warning  = 0.5
  }

  on_missing_data = "default"

  require_full_window = false

  tags = module.synthetics.base_tags
}

resource "datadog_monitor" "on_call_fhir_endpoints" {
  for_each = local.env == "test" ? {} : datadog_synthetics_test.fhir_endpoints

  name    = "[${upper(local.env)}] [${local.app}] On Call — Synthetics ${each.key}"
  type    = "query alert"
  message = <<-EOT
  Synthetics test ${each.value.name} has failed over the ${local.min_failure_duration_for_on_call}.
  EOT

  query = <<-EOT
  sum(${local.min_failure_duration_for_on_call}):sum:synthetics.test_runs{status:failure, check_id:${each.value.id}}.as_count() / sum:synthetics.test_runs{check_id:${each.value.id}}.as_count() >= 1
  EOT

  monitor_thresholds {
    critical = 1
    warning  = 0.5
  }

  on_missing_data = "default"

  require_full_window = false

  tags = module.synthetics.base_tags
}

resource "datadog_monitor" "on_call_userinfo_endpoints" {
  for_each = local.env == "test" ? {} : datadog_synthetics_test.userinfo_endpoints

  name    = "[${upper(local.env)}] [${local.app}] On Call — Synthetics ${each.key}"
  type    = "query alert"
  message = <<-EOT
  Synthetics test ${each.value.name} has failed over the ${local.min_failure_duration_for_on_call}.
  EOT

  query = <<-EOT
  sum(${local.min_failure_duration_for_on_call}):sum:synthetics.test_runs{status:failure, check_id:${each.value.id}}.as_count() / sum:synthetics.test_runs{check_id:${each.value.id}}.as_count() >= 1
  EOT

  monitor_thresholds {
    critical = 1
    warning  = 0.5
  }

  on_missing_data = "default"

  require_full_window = false

  tags = module.synthetics.base_tags
}

resource "datadog_monitor" "on_call_insurance_card_endpoints" {
  for_each = local.env == "test" ? {} : datadog_synthetics_test.insurance_card_endpoints

  name    = "[${upper(local.env)}] [${local.app}] On Call — Synthetics ${each.key}"
  type    = "query alert"
  message = <<-EOT
  Synthetics test ${each.value.name} has failed over the ${local.min_failure_duration_for_on_call}.
  EOT

  query = <<-EOT
  sum(${local.min_failure_duration_for_on_call}):sum:synthetics.test_runs{status:failure, check_id:${each.value.id}}.as_count() / sum:synthetics.test_runs{check_id:${each.value.id}}.as_count() >= 1
  EOT

  monitor_thresholds {
    critical = 1
    warning  = 0.5
  }

  on_missing_data = "default"

  require_full_window = false

  tags = module.synthetics.base_tags
}

locals {
  on_call_all_endpoint_monitors = merge(
    datadog_monitor.on_call_fhir_endpoints,
    datadog_monitor.on_call_userinfo_endpoints,
    datadog_monitor.on_call_insurance_card_endpoints,
  )

  on_call_composite_groups = [
    for version in local.versions : {
      version     = version,
      monitor_ids = [for monitor in local.on_call_all_endpoint_monitors : monitor.id if strcontains(monitor.name, "v${version}")]
    }
  ]
}

resource "datadog_monitor" "on_call_api_endpoints_composite" {
  for_each = local.env == "test" ? {} : {
    for group in local.on_call_composite_groups : "v${group.version}" => group
  }

  name    = "[${upper(local.env)}] [${local.app}] On Call — Synthetics ${each.key} API Endpoints Composite"
  type    = "composite"
  message = <<-EOT
  One or more synthetics tests have failed over the failure duration limit for on call.

  [Contains these tests](https://app.ddog-gov.com/synthetics/tests?query=${urlencode("monitor_id:(${join(" OR ", each.value.monitor_ids)})")}&from_ts={{eval "last_triggered_at_epoch-${local.monitor_config.synthetics.min_failure_duration}*1000"}}&to_ts={{last_triggered_at_epoch}}&live=false)

  ${module.common_datadog_monitors.notify}
  ${module.common_datadog_monitors.victorops_notify}
  EOT

  query = join(" || ", each.value.monitor_ids)

  notify_no_data = true

  require_full_window = false

  tags = module.synthetics.base_tags

  lifecycle {
    precondition {
      condition     = length(each.value.monitor_ids) <= 10
      error_message = "Skipping on call composite monitors due to too many monitors in the composite. Datadog only allows 10 monitors in a composite."
    }
  }
}
