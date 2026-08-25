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
