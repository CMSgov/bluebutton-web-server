locals {
  bb_domain       = trimprefix(local.hostname_url_normalized, "https://")
  medicare_domain = local.env == "test" ? "test.medicare.gov" : "www.medicare.gov"

  _cookies = [
    {
      cookie = data.aws_ssm_parameter.bb_akamai_aca_token.value
      domain = local.bb_domain
      when   = local.env == "test" || local.env == "prod"
    },
    {
      cookie = data.aws_ssm_parameter.medicare_slsx_akamai_aca_token.value
      domain = local.medicare_domain
      when   = local.env == "test"
    },
    {
      cookie = data.aws_ssm_parameter.medicare_gov_synthetic_tests_akamai_token.value
      domain = local.medicare_domain
      when   = local.env == "sandbox" || local.env == "prod"
    }
  ]

  set_cookie = join("\n", [for c in local._cookies : "${c.cookie}; Domain=${c.domain}; Secure; HttpOnly" if c.when])

  versions = ["2", "3"]
}

resource "datadog_synthetics_test" "test_client_auth_flow_and_calls" {
  for_each = toset(local.versions)

  type   = "browser"
  status = "live"
  name   = "${local.app}-${local.env}-testclient-auth-flow-and-calls-v${each.value}"

  message = <<-EOT
  {{! Test result details }}
  Your test {{#is_alert}}failed{{else}}recovered{{/is_alert}} after running for {{eval "synthetics.attributes.result.duration/1000" }}s on the {{#if synthetics.attributes.location.privateLocation}}Private{{else}}Managed{{/if}} Location {{synthetics.attributes.location.id}}.

  {{! Browser device details }}
  {{#with synthetics.attributes.device}}
  It ran on {{name}} ({{browser.type}} browser {{browser.version}} on a {{type}} form factor with a resolution of {{resolution.width}}x{{resolution.height}}).
  {{/with}}

  {{! Steps overview }}
  {{#if synthetics.attributes.count.steps}}
  The test ran {{synthetics.attributes.count.steps.completed}} steps out of {{synthetics.attributes.count.steps.total}}.
  {{/if}}

  {{! Display failed step if alert }}
  {{#is_alert}}
  {{#with synthetics.failed_step}}
  # Failed step
  The step {{description}} failed{{#if url}} on the URL `{{url}}`{{/if}}.
  Error: `{{{failure.message}}}` (`{{failure.code}}` ).
  {{/with}}
  {{/is_alert}}

  {{! Steps list }}
  # Steps
  {{#each synthetics.attributes.result.steps}}
  * **Step {{@index}}**: {{description}}
  Type: `{{type}}`
  Duration: {{duration}}ms
  Status: {{status}}
  {{#if failure}}
  Error: `{{failure.message}}` (`{{failure.code}}`)
  {{/if}}
  {{/each}}

  {{! Display config variables if any }}
  {{#if synthetics.attributes.result.variables.config}}
  # Config Variables
  The test used the following variables:
  {{#each synthetics.attributes.result.variables.config}}
  * **Name:** `{{name}}`
  Type: `{{type}}`
  Value: {{#if secure}}*Obfuscated (value hidden)*{{else}}`{{{value}}}`{{/if}}{{/each}}
  {{/if}}

  {{! List extracted variables across all successful steps }}
  # Extracted variables
  {{#each synthetics.attributes.result.steps}}
  {{#if extractedValue}}
  * **Name**: `{{extractedValue.name}}`
  **Value:** {{#if extractedValue.secure}}*Obfuscated (value hidden)*{{else}}`{{{extractedValue.value}}}`{{/if}}
  {{/if}}
  {{/each}}

  ${module.common_datadog_monitors.notify}
  EOT

  tags       = module.synthetics.base_tags
  locations  = module.synthetics.non_private_location_ids
  device_ids = ["laptop_large"]

  options_list {
    tick_every           = 5 * 60
    monitor_name         = "[${upper(local.env)}] [${local.app}] Synthetics — testclient-auth-flow-and-calls-v${each.value}"
    min_failure_duration = 25 * 60
  }

  request_definition {
    method = "GET"
    # prod does not have a testclient link to click, so we start directly on testclient page
    url = "${local.hostname_url_normalized}%{if local.env == "prod"}/testclient%{endif}"
  }

  set_cookie = local.set_cookie

  browser_variable {
    type    = "text"
    name    = "BBUSER_NUMBER"
    pattern = each.value == "2" ? "00000" : "00123"
  }

  browser_variable {
    type    = "text"
    name    = "SITE"
    pattern = local.hostname_url_normalized
  }

  browser_variable {
    type    = "text"
    name    = "MEDICARE_SITE"
    pattern = "https://${local.medicare_domain}"
  }

  browser_variable {
    type    = "text"
    name    = "API_VERSION"
    pattern = each.value
  }

  dynamic "browser_step" {
    for_each = local.env == "prod" ? [] : [1]

    content {
      name          = "Click on link \"Test Client\""
      type          = "click"
      allow_failure = false
      is_critical   = true
      params {
        element = jsonencode({
          "url" : "{{ SITE }}/",
          "multiLocator" : {
            "ab" : "/*[local-name()=\"html\"][1]/*[local-name()=\"body\"][1]/*[local-name()=\"header\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"nav\"][1]/*[local-name()=\"a\"][5]",
            "at" : "",
            "cl" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" desktop-nav-items \")]/*[local-name()=\"a\"][5]",
            "co" : "[{\"text\":\"test client\",\"textType\":\"directText\"},{\"relation\":\"BEFORE\",\"tagName\":\"A\",\"text\":\" documentation support api reference production access guide test client login signup \",\"textType\":\"innerText\"}]",
            "ro" : "//*[1]/*[local-name()=\"nav\"][1]/*[5]",
            "clt" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" desktop-nav-items \")]/descendant::*[text()[normalize-space(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞŸŽŠŒ', 'abcdefghijklmnopqrstuvwxyzàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿžšœ')) = \"test client\"]]"
          },
          "targetOuterHTML" : "<a href=\"/testclient/\" style=\"outline-color: transparent; background-color: transparent\">Test Client</a>"
        })
      }
    }
  }

  browser_step {
    name          = "Click on link \"Get a Sample Authorization ...\""
    type          = "click"
    allow_failure = false
    is_critical   = true
    params {
      element = jsonencode({
        "url" : "{{ SITE }}/testclient/",
        "multiLocator" : {
          "ab" : "/*[local-name()=\"html\"][1]/*[local-name()=\"body\"][1]/*[local-name()=\"main\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"a\"][${each.value == "2" ? "1" : "2"}]",
          "at" : "",
          "cl" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" ds-c-button \")]",
          "co" : "[{\"text\":\"get a sample authorization token (v{{ API_VERSION }})\",\"textType\":\"directText\"}]",
          "ro" : "//*[@id=\"auth_link_v{{ API_VERSION }}\"]",
          "clt" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" ds-l-lg-col--11 \")]/descendant::*[text()[normalize-space(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞŸŽŠŒ', 'abcdefghijklmnopqrstuvwxyzàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿžšœ')) = \"get a sample authorization token${each.value == "3" ? " (v3)" : ""}\"]]"
        },
        "targetOuterHTML" : "<a id=\"auth_link_v{{ API_VERSION }}\" href=\"/testclient/authorize-link-v{{ API_VERSION }}\" class=\"ds-c-button ds-u-margin-y--2 ds-c-button--solid ds-u-color--white\">Get a Sample Authorization Token${each.value == "3" ? " (v3)" : ""}</a>"
      })
    }
  }

  browser_step {
    name          = "Click on link \"Authorize as a Beneficiary\""
    type          = "click"
    allow_failure = false
    is_critical   = true
    params {
      element = jsonencode({
        "url" : "{{ SITE }}/testclient/authorize-link-v{{ API_VERSION }}",
        "multiLocator" : {
          "ab" : "/*[local-name()=\"html\"][1]/*[local-name()=\"body\"][1]/*[local-name()=\"main\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][2]/*[local-name()=\"a\"][1]",
          "at" : "",
          "cl" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" action-container \")]/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" ds-c-button \")][1]",
          "co" : "[{\"text\":\"authorize as a beneficiary\",\"textType\":\"directText\"}]",
          "ro" : "//*[text()[normalize-space(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞŸŽŠŒ', 'abcdefghijklmnopqrstuvwxyzàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿžšœ')) = \"authorize as a beneficiary\"]]",
          "clt" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" action-container \")]/descendant::*[text()[normalize-space(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞŸŽŠŒ', 'abcdefghijklmnopqrstuvwxyzàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿžšœ')) = \"authorize as a beneficiary\"]]"
        },
        "targetOuterHTML" : "<a href=\"{{ SITE }}/v{{ API_VERSION }}/o/authorize/"
      })
    }
  }

  browser_step {
    name          = "Test active page URL's content"
    type          = "assertCurrentUrl"
    allow_failure = false
    is_critical   = true
    params {
      check = "startsWith"
      value = "{{ MEDICARE_SITE }}/account/login/"
    }
  }

  browser_step {
    name          = "Click on button \"Medicare.gov If you've ...\""
    type          = "click"
    allow_failure = false
    is_critical   = true
    params {
      element = jsonencode({
        "url" : "{{ MEDICARE_SITE }}/account/login/",
        "multiLocator" : {
          "ab" : "/*[local-name()=\"html\"][1]/*[local-name()=\"body\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"main\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][5]/*[local-name()=\"button\"][1]",
          "at" : "",
          "cl" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" acct-u-container--8 \")]/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" ds-c-button \")][4]",
          "co" : "",
          "ro" : "//*[5]/*[local-name()=\"button\"]",
          "clt" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" acct-u-container--8 \")]/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" ds-c-button \")][4]"
        },
        "targetOuterHTML" : "<button type=\"button\" class=\"ds-c-button ds-c-button--ghost ds-l-col--12\"><div class=\"ds-u-align-items--center ds-l-row\"><div class=\"ds-l-col--2 ds-u-padding-y--2\"><img src=\"/account/assets/csp-medica"
      })
    }
  }

  browser_step {
    name          = "Type text on input \"USERNAME\""
    type          = "typeText"
    allow_failure = false
    is_critical   = true
    params {
      value = "BBUser{{ BBUSER_NUMBER }}"
      element = jsonencode({
        "url" : "{{ MEDICARE_SITE }}/account/login/",
        "multiLocator" : {
          "ab" : "/*[local-name()=\"html\"][1]/*[local-name()=\"body\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"main\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"form\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"input\"][1]",
          "at" : "/descendant::*[@name=\"username\" and @type=\"text\"]",
          "cl" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" ds-c-field \")]",
          "co" : "[{\"text\":\"username\",\"textType\":\"innerText\"}]",
          "ro" : "//*[@id=\"text-field--19\"]",
          "clt" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" ds-c-field \")]"
        },
        "targetOuterHTML" : "<input class=\"ds-c-field\" type=\"text\" aria-invalid=\"false\" name=\"username\" autocomplete=\"username webauthn\" id=\"text-field--19\">"
      })
    }
  }

  browser_step {
    name          = "Press key 'Enter'"
    type          = "pressKey"
    allow_failure = false
    is_critical   = true
    params {
      value = "Enter"
    }
  }

  browser_step {
    name          = "Type text on input \"PASSWORD\""
    type          = "typeText"
    allow_failure = false
    is_critical   = true
    params {
      value = "PW{{ BBUSER_NUMBER }}!"
      element = jsonencode({
        "url" : "{{ MEDICARE_SITE }}/account/login/",
        "multiLocator" : {
          "ab" : "/*[local-name()=\"html\"][1]/*[local-name()=\"body\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"main\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"form\"][1]/*[local-name()=\"div\"][3]/*[local-name()=\"div\"][1]/*[local-name()=\"input\"][1]",
          "at" : "/descendant::*[@name=\"password\" and @type=\"password\"]",
          "cl" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" _input_1jd63_12 \")]",
          "co" : "[{\"text\":\"password\",\"textType\":\"innerText\"}]",
          "ro" : "//*[local-name()=\"input\"]",
          "clt" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" _input_1jd63_12 \")]"
        },
        "targetOuterHTML" : "<input class=\"ds-c-field _input_1jd63_12\" type=\"password\" aria-invalid=\"false\" name=\"password\" id=\"text-field--34\">"
      })
    }
  }

  browser_step {
    name          = "Click on button \"Log in\""
    type          = "click"
    allow_failure = false
    is_critical   = true
    params {
      element = jsonencode({
        "url" : "{{ MEDICARE_SITE }}/account/login/",
        "multiLocator" : {
          "ab" : "/*[local-name()=\"html\"][1]/*[local-name()=\"body\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"main\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"form\"][1]/*[local-name()=\"div\"][4]/*[local-name()=\"button\"][1]",
          "at" : "",
          "cl" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" ds-c-button--solid \")]",
          "co" : "[{\"text\":\"log in\",\"textType\":\"directText\"},{\"relation\":\"PARENT OF\",\"tagName\":\"FORM\",\"text\":\"usernamebbuser00000passwordshowforgot your username or password?log inback\",\"textType\":\"innerText\"}]",
          "ro" : "//*[@id=\"login-button\"]",
          "clt" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" ds-c-button--solid \")]"
        },
        "targetOuterHTML" : "<button type=\"submit\" id=\"login-button\" class=\"ds-c-button ds-c-button--solid ds-u-display--flex ds-u-align-items--center gap-1\">Log in</button>"
      })
    }
  }

  browser_step {
    name          = "Test active page URL's content"
    type          = "assertCurrentUrl"
    allow_failure = false
    is_critical   = true
    params {
      check = "startsWith"
      value = "{{ SITE }}/v{{ API_VERSION }}/o/authorize/"
    }
  }

  browser_step {
    name          = "Click on input \"Connect\""
    type          = "click"
    allow_failure = false
    is_critical   = true
    params {
      element = jsonencode({
        "url" : "{{ SITE }}/v{{ API_VERSION }}/o/authorize/",
        "multiLocator" : {
          "ab" : "/*[local-name()=\"html\"][1]/*[local-name()=\"body\"][1]/*[local-name()=\"main\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][2]/*[local-name()=\"div\"][1]/*[local-name()=\"form\"][1]/*[local-name()=\"div\"][2]/*[local-name()=\"input\"][2]",
          "at" : "/descendant::*[@name=\"allow\" and @value=\"Connect\"]",
          "cl" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" ds-c-button--solid \")]",
          "co" : "",
          "ro" : "//*[@id=\"approve\"]",
          "clt" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" ds-c-button--solid \")]"
        },
        "targetOuterHTML" : "<input class=\"ds-c-button ds-c-button--solid\" id=\"approve\" type=\"submit\" name=\"allow\" value=\"Connect\">"
      })
    }
  }

  browser_step {
    name          = "Test active page URL's content"
    type          = "assertCurrentUrl"
    allow_failure = false
    is_critical   = true
    params {
      check = "equals"
      value = "{{ SITE }}/testclient/"
    }
  }

  browser_step {
    name          = "Click on link \"ExplanationOfBenefit\""
    type          = "click"
    allow_failure = false
    is_critical   = true
    params {
      element = jsonencode({
        "url" : "{{ SITE }}/testclient/",
        "multiLocator" : {
          "ab" : "/*[local-name()=\"html\"][1]/*[local-name()=\"body\"][1]/*[local-name()=\"main\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"ul\"][1]/*[local-name()=\"li\"][1]/*[local-name()=\"a\"][1]",
          "at" : "",
          "cl" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" ds-l-lg-col--11 \")]/*[local-name()=\"ul\"][1]/*[local-name()=\"li\"][1]/*[local-name()=\"a\"][1]",
          "co" : "[{\"text\":\"explanationofbenefit\",\"textType\":\"directText\"}]",
          "ro" : "//*[text()[normalize-space(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞŸŽŠŒ', 'abcdefghijklmnopqrstuvwxyzàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿžšœ')) = \"explanationofbenefit\"]]",
          "clt" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" ds-l-lg-col--11 \")]/descendant::*[text()[normalize-space(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞŸŽŠŒ', 'abcdefghijklmnopqrstuvwxyzàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿžšœ')) = \"explanationofbenefit\"]]"
        },
        "targetOuterHTML" : "<a href=\"/testclient/ExplanationOfBenefitV{{ API_VERSION }}\">ExplanationOfBenefit</a>"
      })
    }
  }

  browser_step {
    name          = "Test text is present on at least one page"
    type          = "assertPageContains"
    allow_failure = false
    is_critical   = true
    params {
      value = "Response (Bundle of ExplanationOfBenefit), API version: {{ API_VERSION }}"
    }
  }

  browser_step {
    name          = "Test text is present on at least one page"
    type          = "assertPageContains"
    allow_failure = false
    is_critical   = true
    params {
      value = "\"resourceType\": \"Bundle\""
    }
  }

  browser_step {
    name          = "Test text is present on at least one page"
    type          = "assertPageContains"
    allow_failure = false
    is_critical   = true
    params {
      value = "\"type\": \"searchset\""
    }
  }

  browser_step {
    name          = "Test text is present on at least one page"
    type          = "assertPageContains"
    allow_failure = false
    is_critical   = true
    params {
      value = "\"resourceType\": \"ExplanationOfBenefit\""
    }
  }

  browser_step {
    name          = "Navigate to link"
    type          = "goToUrl"
    allow_failure = false
    is_critical   = true
    params {
      value = "{{ SITE }}/testclient/"
    }
  }

  browser_step {
    name          = "Click on link \"Patient\""
    type          = "click"
    allow_failure = false
    is_critical   = true
    params {
      element = jsonencode({
        "url" : "{{ SITE }}/testclient/",
        "multiLocator" : {
          "ab" : "/*[local-name()=\"html\"][1]/*[local-name()=\"body\"][1]/*[local-name()=\"main\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"ul\"][1]/*[local-name()=\"li\"][2]/*[local-name()=\"a\"][1]",
          "at" : "",
          "cl" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" ds-l-lg-col--11 \")]/*[local-name()=\"ul\"][1]/*[local-name()=\"li\"][2]/*[local-name()=\"a\"][1]",
          "co" : "[{\"text\":\"patient\",\"textType\":\"directText\"}]",
          "ro" : "//*[text()[normalize-space(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞŸŽŠŒ', 'abcdefghijklmnopqrstuvwxyzàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿžšœ')) = \"patient\"]]",
          "clt" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" ds-l-lg-col--11 \")]/descendant::*[text()[normalize-space(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞŸŽŠŒ', 'abcdefghijklmnopqrstuvwxyzàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿžšœ')) = \"patient\"]]"
        },
        "targetOuterHTML" : "<a href=\"/testclient/PatientV{{ API_VERSION }}\">Patient</a>"
      })
    }
  }

  browser_step {
    name          = "Test text is present on at least one page"
    type          = "assertPageContains"
    allow_failure = false
    is_critical   = true
    params {
      value = "Response (Patient), API version: {{ API_VERSION }}"
    }
  }

  browser_step {
    name          = "Test text is present on at least one page"
    type          = "assertPageContains"
    allow_failure = false
    is_critical   = true
    params {
      value = "\"resourceType\": \"Patient\""
    }
  }

  browser_step {
    name          = "Test text is present on at least one page"
    type          = "assertPageContains"
    allow_failure = false
    is_critical   = true
    params {
      value = "\"name\":"
    }
  }

  browser_step {
    name          = "Navigate to link"
    type          = "goToUrl"
    allow_failure = false
    is_critical   = true
    params {
      value = "{{ SITE }}/testclient/"
    }
  }

  browser_step {
    name          = "Click on link \"Coverage\""
    type          = "click"
    allow_failure = false
    is_critical   = true
    params {
      element = jsonencode({
        "url" : "{{ SITE }}/testclient/",
        "multiLocator" : {
          "ab" : "/*[local-name()=\"html\"][1]/*[local-name()=\"body\"][1]/*[local-name()=\"main\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"ul\"][1]/*[local-name()=\"li\"][3]/*[local-name()=\"a\"][1]",
          "at" : "",
          "cl" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" ds-l-lg-col--11 \")]/*[local-name()=\"ul\"][1]/*[local-name()=\"li\"][3]/*[local-name()=\"a\"][1]",
          "co" : "[{\"text\":\"coverage\",\"textType\":\"directText\"}]",
          "ro" : "//*[text()[normalize-space(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞŸŽŠŒ', 'abcdefghijklmnopqrstuvwxyzàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿžšœ')) = \"coverage\"]]",
          "clt" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" ds-l-lg-col--11 \")]/descendant::*[text()[normalize-space(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞŸŽŠŒ', 'abcdefghijklmnopqrstuvwxyzàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿžšœ')) = \"coverage\"]]"
        },
        "targetOuterHTML" : "<a href=\"/testclient/CoverageV{{ API_VERSION }}\">Coverage</a>"
      })
    }
  }

  browser_step {
    name          = "Test text is present on at least one page"
    type          = "assertPageContains"
    allow_failure = false
    is_critical   = true
    params {
      value = "Response (Bundle of Coverage), API version: {{ API_VERSION }}"
    }
  }

  browser_step {
    name          = "Test text is present on at least one page"
    type          = "assertPageContains"
    allow_failure = false
    is_critical   = true
    params {
      value = "\"resourceType\": \"Coverage\""
    }
  }

  browser_step {
    name          = "Navigate to link"
    type          = "goToUrl"
    allow_failure = false
    is_critical   = true
    params {
      value = "{{ SITE }}/testclient/"
    }
  }

  browser_step {
    name          = "Click on link \"Profile\""
    type          = "click"
    allow_failure = false
    is_critical   = true
    params {
      element = jsonencode({
        "url" : "{{ SITE }}/testclient/",
        "multiLocator" : {
          "ab" : "/*[local-name()=\"html\"][1]/*[local-name()=\"body\"][1]/*[local-name()=\"main\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"ul\"][1]/*[local-name()=\"li\"][4]/*[local-name()=\"a\"][1]",
          "at" : "",
          "cl" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" ds-l-lg-col--11 \")]/*[local-name()=\"ul\"][1]/*[local-name()=\"li\"][4]/*[local-name()=\"a\"][1]",
          "co" : "[{\"text\":\"profile\",\"textType\":\"directText\"}]",
          "ro" : "//*[text()[normalize-space(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞŸŽŠŒ', 'abcdefghijklmnopqrstuvwxyzàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿžšœ')) = \"profile\"]]",
          "clt" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" ds-l-lg-col--11 \")]/descendant::*[text()[normalize-space(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞŸŽŠŒ', 'abcdefghijklmnopqrstuvwxyzàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿžšœ')) = \"profile\"]]"
        },
        "targetOuterHTML" : "<a href=\"/testclient/userinfoV{{ API_VERSION }}\">Profile </a>"
      })
    }
  }

  browser_step {
    name          = "Test text is present on at least one page"
    type          = "assertPageContains"
    allow_failure = false
    is_critical   = true
    params {
      value = "Response (Profile (OIDC Userinfo)), API version: {{ API_VERSION }}"
    }
  }

  browser_step {
    name          = "Test text is present on at least one page"
    type          = "assertPageContains"
    allow_failure = false
    is_critical   = true
    params {
      value = "\"sub\": "
    }
  }

  browser_step {
    name          = "Test text is present on at least one page"
    type          = "assertPageContains"
    allow_failure = false
    is_critical   = true
    params {
      value = "\"name\": "
    }
  }

  browser_step {
    name          = "Test text is present on at least one page"
    type          = "assertPageContains"
    allow_failure = false
    is_critical   = true
    params {
      value = "\"patient\": "
    }
  }

  browser_step {
    name          = "Navigate to link"
    type          = "goToUrl"
    allow_failure = false
    is_critical   = true
    params {
      value = "{{ SITE }}/testclient/"
    }
  }

  browser_step {
    name          = "Click on link \"FHIR Metadata\""
    type          = "click"
    allow_failure = false
    is_critical   = true
    params {
      element = jsonencode({
        "url" : "{{ SITE }}/testclient/",
        "multiLocator" : {
          "ab" : "/*[local-name()=\"html\"][1]/*[local-name()=\"body\"][1]/*[local-name()=\"main\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"ul\"][1]/*[local-name()=\"li\"][5]/*[local-name()=\"a\"][1]",
          "at" : "",
          "cl" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" ds-l-lg-col--11 \")]/*[local-name()=\"ul\"][1]/*[local-name()=\"li\"][5]/*[local-name()=\"a\"][1]",
          "co" : "[{\"text\":\"fhir metadata\",\"textType\":\"directText\"}]",
          "ro" : "//*[text()[normalize-space(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞŸŽŠŒ', 'abcdefghijklmnopqrstuvwxyzàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿžšœ')) = \"fhir metadata\"]]",
          "clt" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" ds-l-lg-col--11 \")]/descendant::*[text()[normalize-space(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞŸŽŠŒ', 'abcdefghijklmnopqrstuvwxyzàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿžšœ')) = \"fhir metadata\"]]"
        },
        "targetOuterHTML" : "<a href=\"/testclient/metadataV{{ API_VERSION }}?format=json\">FHIR Metadata</a>"
      })
    }
  }

  browser_step {
    name          = "Test text is present on at least one page"
    type          = "assertPageContains"
    allow_failure = false
    is_critical   = true
    params {
      value = "Response (FHIR Metadata), API version: {{ API_VERSION }}"
    }
  }

  browser_step {
    name          = "Test text is present on at least one page"
    type          = "assertPageContains"
    allow_failure = false
    is_critical   = true
    params {
      value = "\"resourceType\": \"CapabilityStatement\""
    }
  }

  browser_step {
    name = "Test text is present on at least one page"
    type = "assertPageContains"
    # allow_failure = false
    # is_critical   = true
    # TODO v3 doesn't have what you'd think here
    allow_failure = each.value == "3"
    is_critical   = each.value == "2"
    params {
      value = "\"publisher\": \"Centers for Medicare & Medicaid Services\""
    }
  }

  browser_step {
    name          = "Navigate to link"
    type          = "goToUrl"
    allow_failure = false
    is_critical   = true
    params {
      value = "{{ SITE }}/testclient/"
    }
  }

  browser_step {
    name          = "Click on link \"OIDC Discovery\""
    type          = "click"
    allow_failure = false
    is_critical   = true
    params {
      element = jsonencode({
        "url" : "{{ SITE }}/testclient/",
        "multiLocator" : {
          "ab" : "/*[local-name()=\"html\"][1]/*[local-name()=\"body\"][1]/*[local-name()=\"main\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"div\"][1]/*[local-name()=\"ul\"][1]/*[local-name()=\"li\"][6]/*[local-name()=\"a\"][1]",
          "at" : "",
          "cl" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" ds-l-lg-col--11 \")]/*[local-name()=\"ul\"][1]/*[local-name()=\"li\"][6]/*[local-name()=\"a\"][1]",
          "co" : "[{\"text\":\"oidc discovery\",\"textType\":\"directText\"}]",
          "ro" : "//*[text()[normalize-space(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞŸŽŠŒ', 'abcdefghijklmnopqrstuvwxyzàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿžšœ')) = \"oidc discovery\"]]",
          "clt" : "/descendant::*[contains(concat(' ', normalize-space(@class), ' '), \" ds-l-lg-col--11 \")]/descendant::*[text()[normalize-space(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞŸŽŠŒ', 'abcdefghijklmnopqrstuvwxyzàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿžšœ')) = \"oidc discovery\"]]"
        },
        "targetOuterHTML" : "<a href=\"/testclient/openidConfigV{{ API_VERSION }}\">OIDC Discovery</a>"
      })
    }
  }

  browser_step {
    name          = "Test text is present on at least one page"
    type          = "assertPageContains"
    allow_failure = false
    is_critical   = true
    params {
      value = "Response (OIDC Discovery), API version: {{ API_VERSION }}"
    }
  }

  browser_step {
    name          = "Test text is present on at least one page"
    type          = "assertPageContains"
    allow_failure = false
    is_critical   = true
    params {
      value = "\"issuer\": \"{{ SITE }}\""
    }
  }
}
