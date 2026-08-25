locals {
  # TODO other endpoints?
  fhir_endpoints = [
    "ExplanationOfBenefit",
    "Patient",
    "Coverage",
  ]

  bb_users = {
    "00000" : data.aws_ssm_parameter.datadog_bbuser00000_access_token_global_variable_id.value,
    "10000" : data.aws_ssm_parameter.datadog_bbuser10000_access_token_global_variable_id.value,
  }

  fhir_endpoint_tests = [
    for product in setproduct(
      local.fhir_endpoints,
      local.versions,
      keys(local.bb_users)
      ) : {
      endpoint = product[0],
      version  = product[1],
      bb_user  = { key = product[2], value = local.bb_users[product[2]] }
    }
  ]
}

resource "datadog_synthetics_test" "fhir_endpoints" {
  for_each = { for obj in local.fhir_endpoint_tests : "${local.app}-${local.env}-v${obj.version}-${obj.endpoint}-BBUser${obj.bb_user.key}" => obj }

  name    = each.key
  type    = "api"
  subtype = "http"
  status  = "live"
  message = "Synthetics test ${each.key} has failed. ${module.common_datadog_monitors.notify}"

  locations = module.synthetics.non_private_location_ids

  options_list {
    tick_every           = 60
    monitor_name         = "[${upper(local.env)}] [${local.app}] Synthetics — ${each.key}"
    min_failure_duration = local.monitor_config.synthetics.min_failure_duration
  }

  tags = module.synthetics.base_tags

  config_variable {
    name = "BBUSER${each.value.bb_user.key}_${upper(local.env)}_ACCESS_TOKEN"
    type = "global"
    id   = each.value.bb_user.value
  }

  # TODO should we use a global variable instead?
  dynamic "config_variable" {
    for_each = local.env == "test" ? [1] : []
    content {
      name    = "AKAMAI_COOKIE"
      type    = "text"
      secure  = true
      pattern = data.aws_ssm_parameter.bb_akamai_aca_token.value
    }
  }

  request_headers = merge(
    { Authorization = "Bearer {{ BBUSER00000_${upper(local.env)}_ACCESS_TOKEN }}" },
    local.env == "test" ? { cookie = "{{ AKAMAI_COOKIE }}" } : {}
  )

  request_definition {
    method = "GET"
    url    = "${local.hostname_url_normalized}/v${each.value.version}/fhir/${each.value.endpoint}"
  }

  assertion {
    type     = "responseTime"
    operator = "lessThan"
    target   = "2000"
  }

  assertion {
    type     = "statusCode"
    operator = "is"
    target   = "200"
  }

  assertion {
    type     = "header"
    operator = "is"
    target   = "application/fhir+json"
    property = "content-type"
  }

  assertion {
    type     = "body"
    operator = "validatesJSONPath"
    targetjsonpath {
      jsonpath         = "$.resourceType"
      operator         = "is"
      targetvalue      = "Bundle"
      elementsoperator = "everyElementMatches"
    }
  }

  assertion {
    type     = "body"
    operator = "validatesJSONPath"
    targetjsonpath {
      jsonpath         = "$.type"
      operator         = "is"
      targetvalue      = "searchset"
      elementsoperator = "everyElementMatches"
    }
  }

  assertion {
    type     = "body"
    operator = "validatesJSONPath"
    targetjsonpath {
      jsonpath         = "$.id"
      operator         = "matches"
      targetvalue      = "^[0-9a-zA-Z]{8}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{12}$" # a UUID
      elementsoperator = "everyElementMatches"
    }
  }

  assertion {
    type     = "body"
    operator = "validatesJSONPath"
    targetjsonpath {
      jsonpath         = "$.entry[*].resource.id"
      operator         = "matches"
      targetvalue      = "^([\\w-]+-)?-\\d+$" # a negative number, possibly preceeded with some claim type and another dash
      elementsoperator = "everyElementMatches"
    }
  }

  assertion {
    type     = "body"
    operator = "validatesJSONPath"
    targetjsonpath {
      jsonpath         = "$.entry[*].resource.resourceType"
      operator         = "is"
      targetvalue      = each.value.endpoint
      elementsoperator = "everyElementMatches"
    }
  }
}
