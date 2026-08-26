locals {
  fhir_endpoints = [
    "ExplanationOfBenefit",
    "Patient",
    "Coverage",
  ]

  bb_users = {
    "00000" : data.aws_ssm_parameter.datadog_bbuser00000_access_token.value,
    "10000" : data.aws_ssm_parameter.datadog_bbuser10000_access_token.value,
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
    type = "text"
    secure = true
    pattern   = each.value.bb_user.value
  }

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
    { Authorization = "Bearer {{ BBUSER${each.value.bb_user.key}_${upper(local.env)}_ACCESS_TOKEN }}" },
    local.env == "test" ? { cookie = "{{ AKAMAI_COOKIE }}" } : {}
  )

  request_definition {
    method = "GET"
    url    = "${local.hostname_url_normalized}/v${each.value.version}/fhir/${each.value.endpoint}"
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

locals {
  userinfo_endpoint_tests = [
    for product in setproduct(
      local.versions,
      keys(local.bb_users)
      ) : {
      version = product[0],
      bb_user = { key = product[1], value = local.bb_users[product[1]] }
    }
  ]
}

resource "datadog_synthetics_test" "userinfo_endpoints" {
  for_each = { for obj in local.userinfo_endpoint_tests : "${local.app}-${local.env}-v${obj.version}-userinfo-BBUser${obj.bb_user.key}" => obj }

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
    type = "text"
    secure = true
    pattern   = each.value.bb_user.value
  }

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
    { Authorization = "Bearer {{ BBUSER${each.value.bb_user.key}_${upper(local.env)}_ACCESS_TOKEN }}" },
    local.env == "test" ? { cookie = "{{ AKAMAI_COOKIE }}" } : {}
  )

  request_definition {
    method = "GET"
    url    = "${local.hostname_url_normalized}/v${each.value.version}/connect/userinfo"
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
    operator = "validatesJSONPath"
    targetjsonpath {
      jsonpath         = "$.sub"
      operator         = "matches"
      targetvalue      = "^-\\d+$" # a negative number
      elementsoperator = "everyElementMatches"
    }
  }

  assertion {
    type     = "body"
    operator = "validatesJSONPath"
    targetjsonpath {
      jsonpath         = "$.patient"
      operator         = "matches"
      targetvalue      = "^-\\d+$" # a negative number
      elementsoperator = "everyElementMatches"
    }
  }
}

locals {
  insurance_card_versions = ["3"]

  insurance_card_endpoint_tests = [
    for product in setproduct(
      local.insurance_card_versions,
      keys(local.bb_users)
      ) : {
      version = product[0],
      bb_user = { key = product[1], value = local.bb_users[product[1]] }
    }
  ]
}

resource "datadog_synthetics_test" "insurance_card_endpoints" {
  for_each = { for obj in local.insurance_card_endpoint_tests : "${local.app}-${local.env}-v${obj.version}-insurance-card-BBUser${obj.bb_user.key}" => obj }

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
    type = "text"
    secure = true
    pattern   = each.value.bb_user.value
  }

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
    { Authorization = "Bearer {{ BBUSER${each.value.bb_user.key}_${upper(local.env)}_ACCESS_TOKEN }}" },
    local.env == "test" ? { cookie = "{{ AKAMAI_COOKIE }}" } : {}
  )

  request_definition {
    method = "GET"
    url    = "${local.hostname_url_normalized}/v${each.value.version}/fhir/Patient/$generate-insurance-card"
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
      jsonpath         = "$.entry[*].resource.resourceType"
      operator         = "is"
      targetvalue      = "Patient"
      elementsoperator = "atLeastOneElementMatches"
    }
  }
}
