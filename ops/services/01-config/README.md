# Config Service

## Overview

SOPS-managed configuration layer. Decrypts encrypted `.sopsw.yaml` files and provisions SSM parameters for application use.

## How It Works

1. Encrypted values are stored in `values/{parent_env}.sopsw.yaml` (KMS-encrypted, safe for git)
2. The local `sops` module decrypts values at plan/apply time using the `sopsw` wrapper script
3. Decrypted values are provisioned as SSM parameters:
   - Paths containing `nonsensitive` → SSM `String`
   - All other paths → SSM `SecureString` (KMS-encrypted)

## Usage

```bash
cd ops/services/01-config

# Initialize
tofu init -var="parent_env=test"
tofu workspace select test

# Edit encrypted config
bin/sopsw -e values/test.sopsw.yaml

# Plan and apply
tofu plan
tofu apply
```

## Dependencies

| Upstream | What it provides |
|----------|-----------------|
| `00-bootstrap` | KMS key (`alias/bb-{env}-app-key-alias`) |

## Values Files

```
values/
├── .sops.yaml              # SOPS creation rules (KMS key per environment)
├── test.sopsw.yaml         # Encrypted config for test
├── sandbox.sopsw.yaml      # Encrypted config for sandbox
└── prod.sopsw.yaml         # Encrypted config for prod
```

<!-- BEGIN_TF_DOCS -->
<!--WARNING: GENERATED CONTENT with terraform-docs, e.g.
     'terraform-docs --config "$(git rev-parse --show-toplevel)/.terraform-docs.yml" .'
     Manually updating sections between TF_DOCS tags may be overwritten.
     See https://terraform-docs.io/user-guide/configuration/ for more information.
-->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.0 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 6 |

<!--WARNING: GENERATED CONTENT with terraform-docs, e.g.
     'terraform-docs --config "$(git rev-parse --show-toplevel)/.terraform-docs.yml" .'
     Manually updating sections between TF_DOCS tags may be overwritten.
     See https://terraform-docs.io/user-guide/configuration/ for more information.
-->
## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
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
|------|--------|---------|
| <a name="module_platform"></a> [platform](#module\_platform) | ../../modules/platform | n/a |
| <a name="module_sops"></a> [sops](#module\_sops) | ../../modules/sops | n/a |

<!--WARNING: GENERATED CONTENT with terraform-docs, e.g.
     'terraform-docs --config "$(git rev-parse --show-toplevel)/.terraform-docs.yml" .'
     Manually updating sections between TF_DOCS tags may be overwritten.
     See https://terraform-docs.io/user-guide/configuration/ for more information.
-->
## Resources

No resources.

<!--WARNING: GENERATED CONTENT with terraform-docs, e.g.
     'terraform-docs --config "$(git rev-parse --show-toplevel)/.terraform-docs.yml" .'
     Manually updating sections between TF_DOCS tags may be overwritten.
     See https://terraform-docs.io/user-guide/configuration/ for more information.
-->
## Outputs

| Name | Description |
|------|-------------|
| <a name="output_parameter_count"></a> [parameter\_count](#output\_parameter\_count) | Number of SSM parameters provisioned |
| <a name="output_sopsw"></a> [sopsw](#output\_sopsw) | Command to edit the current environment's encrypted values file |
| <a name="output_ssm_parameters"></a> [ssm\_parameters](#output\_ssm\_parameters) | SSM parameters provisioned from SOPS config |
<!-- END_TF_DOCS -->