## Requirements

| Name | Version |
| ---- | ------- |
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.8 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 6 |
| <a name="requirement_datadog"></a> [datadog](#requirement\_datadog) | ~> 4.4 |

## Providers

| Name | Version |
| ---- | ------- |
| <a name="provider_aws"></a> [aws](#provider\_aws) | 6.51.0 |

## Modules

| Name | Source | Version |
| ---- | ------ | ------- |
| <a name="module_common_datadog_monitors"></a> [common\_datadog\_monitors](#module\_common\_datadog\_monitors) | github.com/CMSgov/cdap/terraform/modules/datadog_monitors | 6ded520857376f46bb317dca898e5df6a9ecc93b |
| <a name="module_platform"></a> [platform](#module\_platform) | ../../modules/platform | n/a |

## Resources

| Name | Type |
| ---- | ---- |
| [aws_secretsmanager_secret_version.datadog_cicd_api_key](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/secretsmanager_secret_version) | data source |
| [aws_secretsmanager_secret_version.datadog_cicd_application_key](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/secretsmanager_secret_version) | data source |
| [aws_ssm_parameter.bcda_account_id](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/ssm_parameter) | data source |

## Inputs

| Name | Description | Type | Default | Required |
| ---- | ----------- | ---- | ------- | :------: |
| <a name="input_parent_env"></a> [parent\_env](#input\_parent\_env) | The parent environment of the current solution. Will correspond with `terraform.workspace`.<br/>Necessary on `tofu init` and `tofu workspace select` \_only\_. In all other situations, parent env<br/>will be divined from `terraform.workspace`. | `string` | `null` | no |
| <a name="input_region"></a> [region](#input\_region) | AWS region for resources | `string` | `"us-east-1"` | no |
| <a name="input_root_module"></a> [root\_module](#input\_root\_module) | Root module URL for tracking (e.g., GitHub URL) | `string` | `"https://github.com/CMSgov/bluebutton-web-server"` | no |
| <a name="input_secondary_region"></a> [secondary\_region](#input\_secondary\_region) | Secondary AWS region for DR/failover | `string` | `"us-west-2"` | no |

## Outputs

No outputs.
