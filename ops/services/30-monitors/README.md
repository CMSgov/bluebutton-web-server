# Monitors Layer

## Overview

Datadog monitors created using the CDAP shared monitors module.

See https://github.com/CMSgov/cdap/tree/main/terraform/modules/datadog_monitors for info about the module.

## Resources Managed

- **Datadog monitors** per resource

## Configuration

YAML files in `ops/services/30-monitors/config`:
1. `{env}.yml`
2. `defaults.yml`

<!-- BEGIN_TF_DOCS -->
<!--WARNING: GENERATED CONTENT with terraform-docs, e.g.
     'terraform-docs --config "$(git rev-parse --show-toplevel)/.terraform-docs.yml" .'
     Manually updating sections between TF_DOCS tags may be overwritten.
     See https://terraform-docs.io/user-guide/configuration/ for more information.
-->
## Requirements

| Name | Version |
| ---- | ------- |
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.8 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 6 |
| <a name="requirement_datadog"></a> [datadog](#requirement\_datadog) | ~> 4.4 |

<!--WARNING: GENERATED CONTENT with terraform-docs, e.g.
     'terraform-docs --config "$(git rev-parse --show-toplevel)/.terraform-docs.yml" .'
     Manually updating sections between TF_DOCS tags may be overwritten.
     See https://terraform-docs.io/user-guide/configuration/ for more information.
-->
## Inputs

| Name | Description | Type | Default | Required |
| ---- | ----------- | ---- | ------- | :------: |
| <a name="input_parent_env"></a> [parent\_env](#input\_parent\_env) | The parent environment of the current solution. Will correspond with `terraform.workspace`.<br/>Necessary on `tofu init` and `tofu workspace select` \_only\_. In all other situations, parent env<br/>will be divined from `terraform.workspace`. | `string` | `null` | no |
| <a name="input_region"></a> [region](#input\_region) | AWS region for resources | `string` | `"us-east-1"` | no |
| <a name="input_root_module"></a> [root\_module](#input\_root\_module) | Root module URL for tracking (e.g., GitHub URL) | `string` | `"https://github.com/CMSgov/bluebutton-web-server"` | no |
| <a name="input_secondary_region"></a> [secondary\_region](#input\_secondary\_region) | Secondary AWS region for DR/failover | `string` | `"us-west-2"` | no |

<!--WARNING: GENERATED CONTENT with terraform-docs, e.g.
     'terraform-docs --config "$(git rev-parse --show-toplevel)/.terraform-docs.yml" .'
     Manually updating sections between TF_DOCS tags may be overwritten.
     See https://terraform-docs.io/user-guide/configuration/ for more information.
-->
## Modules

| Name | Source | Version |
| ---- | ------ | ------- |
| <a name="module_common_datadog_monitors"></a> [common\_datadog\_monitors](#module\_common\_datadog\_monitors) | github.com/CMSgov/cdap/terraform/modules/datadog_monitors | b95ffb3cc482cda83ae46c8f3438a348ff9a4272 |
| <a name="module_platform"></a> [platform](#module\_platform) | ../../modules/platform | n/a |
| <a name="module_synthetics"></a> [synthetics](#module\_synthetics) | github.com/CMSgov/cdap/terraform/modules/datadog_synthetics | b95ffb3cc482cda83ae46c8f3438a348ff9a4272 |

<!--WARNING: GENERATED CONTENT with terraform-docs, e.g.
     'terraform-docs --config "$(git rev-parse --show-toplevel)/.terraform-docs.yml" .'
     Manually updating sections between TF_DOCS tags may be overwritten.
     See https://terraform-docs.io/user-guide/configuration/ for more information.
-->
## Resources

| Name | Type |
| ---- | ---- |
| [datadog_monitor.on_call_health](https://registry.terraform.io/providers/datadog/datadog/latest/docs/resources/monitor) | resource |
| [datadog_synthetics_test.health](https://registry.terraform.io/providers/datadog/datadog/latest/docs/resources/synthetics_test) | resource |
| [datadog_synthetics_test.homepage_uptime](https://registry.terraform.io/providers/datadog/datadog/latest/docs/resources/synthetics_test) | resource |
| [datadog_synthetics_test.static_site_uptime](https://registry.terraform.io/providers/datadog/datadog/latest/docs/resources/synthetics_test) | resource |
| [aws_secretsmanager_secret_version.datadog_cicd_api_key](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/secretsmanager_secret_version) | data source |
| [aws_secretsmanager_secret_version.datadog_cicd_application_key](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/secretsmanager_secret_version) | data source |
| [aws_ssm_parameter.bb_akamai_aca_token](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/ssm_parameter) | data source |
| [aws_ssm_parameter.bcda_account_id](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/ssm_parameter) | data source |
| [aws_ssm_parameter.hostname_url](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/ssm_parameter) | data source |
| [aws_ssm_parameter.medicare_gov_synthetic_tests_akamai_token](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/ssm_parameter) | data source |
| [aws_ssm_parameter.medicare_slsx_akamai_aca_token](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/ssm_parameter) | data source |

<!--WARNING: GENERATED CONTENT with terraform-docs, e.g.
     'terraform-docs --config "$(git rev-parse --show-toplevel)/.terraform-docs.yml" .'
     Manually updating sections between TF_DOCS tags may be overwritten.
     See https://terraform-docs.io/user-guide/configuration/ for more information.
-->
## Outputs

No outputs.
<!-- END_TF_DOCS -->
