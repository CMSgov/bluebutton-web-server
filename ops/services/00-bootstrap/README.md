# Bootstrap Service

## Overview

Foundational infrastructure layer that provides shared resources required by all other services in the Blue Button environment.

## Resources Managed

### Container Infrastructure
- **ECR Repositories**: Docker image storage for application containers
- **KMS Keys**: Encryption keys for ECR and other services

### CI/CD Infrastructure  
- **CodeBuild Projects**: GitHub Actions runner integration
- **GitHub OIDC Provider**: Secure authentication for GitHub Actions workflows
- **IAM Roles**: 
  - CodeBuild service role with ECR/CloudWatch/GitHub permissions
  - GitHub Actions deployment role with OIDC trust

### Networking & Connectivity
- **GitHub CodeStar Connection**: Authenticated GitHub repository access
- **CloudWatch Log Groups**: CodeBuild execution logs

## Architecture

```
┌─────────────────────────────────────────┐
│         00-bootstrap                     │
├─────────────────────────────────────────┤
│                                          │
│  ECR Repos  ──┐                         │
│  KMS Keys   ──┼── Shared by all envs    │
│  CodeBuild  ──┤   (prod/sandbox)        │
│  OIDC       ──┘                         │
│                                          │
└─────────────────────────────────────────┘
         ▲              ▲
         │              │
    Test Account   Prod Account
    (separate)     (prod + sandbox)
```

## Environment Strategy

- **Test**: Separate AWS account, creates own resources
- **Prod**: Creates resources in prod account
- **Sandbox**: Reuses prod account resources (no creation)

## Initialization

### Prerequisites
1. S3 buckets must exist:
   - `bb-test-app-config` (Test account)
   - `bb-prod-app-config` (Prod account, shared by sandbox)

2. AWS credentials configured for target environment

### First-Time Setup

```bash
cd ops/services/00-bootstrap

# Initialize (parent_env determines S3 bucket for state)
tofu init -var="parent_env=prod"

# Select workspace
tofu workspace select prod

# Plan and apply
tofu plan
tofu apply
```

### Manual Post-Deployment Steps

1. **Confirm GitHub Connection**
   - Navigate to AWS Console → Developer Tools → Settings → Connections
   - Find `bb-github-connection`
   - Click "Update pending connection" and authorize GitHub access

2. **Configure GitHub Actions Secrets**
   - Add the GitHub Actions role ARN to your repository secrets:
     ```bash
     AWS_ROLE_ARN: <github_actions_role_arn from outputs>
     ```

## Outputs

Key outputs for downstream services:

- `ecr_repository_url` — Container image registry URL
- `ecr_repository_arn` — ECR repository ARN
- `ecr_kms_key_arn` — KMS key used for ECR encryption
- `env_kms_key_arn` / `env_kms_key_alias` — Pre-existing environment KMS key
- `codebuild_project_arn` / `codebuild_project_name` — CodeBuild project
- `github_oidc_provider_arn` — OIDC provider for GitHub Actions
- `github_actions_role_arn` / `github_actions_role_name` — GitHub Actions deployment role
- `github_connection_arn` — GitHub CodeStar connection

## Dependencies

- **Platform Module**: `../../modules/platform` (VPC, subnets, KMS discovery)
- **Root Config**: `../root.tofu.tf` (symlinked as `tofu.tf`)

## File Structure

```
00-bootstrap/
├── main.tf              # Platform module, ECR repositories, KMS keys
├── codebuild.tf         # CodeBuild project, GitHub connection
├── codebuild_iam.tf     # CodeBuild IAM role and policies
├── oidc.tf              # GitHub Actions OIDC provider and role
├── outputs.tf           # Resource outputs
├── variables.tf         # Input variables
└── tofu.tf             # Symlink to ../root.tofu.tf
```

## Notes

- Bootstrap must be applied before all other services
- Resources are shared between prod and sandbox (same AWS account)
- Sandbox workspace skips resource creation (`local.create_resources = false`), reuses prod resources
- ECR lifecycle policy keeps last 30 tagged images
- KMS encryption on state backend is planned but not yet enabled

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
| <a name="input_github_org"></a> [github\_org](#input\_github\_org) | GitHub organization name | `string` | `"CMSgov"` | no |
| <a name="input_github_repo"></a> [github\_repo](#input\_github\_repo) | GitHub repository name (without org) | `string` | `"bluebutton-web-server"` | no |
| <a name="input_github_repo_url"></a> [github\_repo\_url](#input\_github\_repo\_url) | GitHub repository URL for CodeBuild | `string` | `"https://github.com/CMSgov/bluebutton-web-server"` | no |
| <a name="input_iam_path"></a> [iam\_path](#input\_iam\_path) | IAM path for roles | `string` | `"/"` | no |
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

<!--WARNING: GENERATED CONTENT with terraform-docs, e.g.
     'terraform-docs --config "$(git rev-parse --show-toplevel)/.terraform-docs.yml" .'
     Manually updating sections between TF_DOCS tags may be overwritten.
     See https://terraform-docs.io/user-guide/configuration/ for more information.
-->
## Resources

| Name | Type |
|------|------|
| [aws_cloudwatch_log_group.runner](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) | resource |
| [aws_codebuild_project.main](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/codebuild_project) | resource |
| [aws_codebuild_source_credential.github](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/codebuild_source_credential) | resource |
| [aws_codebuild_webhook.runner](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/codebuild_webhook) | resource |
| [aws_codestarconnections_connection.github](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/codestarconnections_connection) | resource |
| [aws_ecr_lifecycle_policy.api](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecr_lifecycle_policy) | resource |
| [aws_ecr_repository.api](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecr_repository) | resource |
| [aws_iam_openid_connect_provider.github_actions](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_openid_connect_provider) | resource |
| [aws_iam_role.codebuild](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role.github_actions](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role_policy.ecr](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy) | resource |
| [aws_iam_role_policy.github](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy) | resource |
| [aws_iam_role_policy.github_actions_codebuild](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy) | resource |
| [aws_iam_role_policy.github_actions_ecr](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy) | resource |
| [aws_iam_role_policy.kms](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy) | resource |
| [aws_iam_role_policy.logs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy) | resource |
| [aws_kms_alias.ecr](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_alias) | resource |
| [aws_kms_key.ecr](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_key) | resource |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity) | data source |
| [aws_iam_policy_document.assume_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_policy_document.ecr](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_policy_document.github](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_policy_document.github_actions_assume_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_policy_document.github_actions_codebuild](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_policy_document.github_actions_ecr](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_policy_document.kms](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_policy_document.logs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_kms_alias.env](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/kms_alias) | data source |
| [aws_region.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/region) | data source |

<!--WARNING: GENERATED CONTENT with terraform-docs, e.g.
     'terraform-docs --config "$(git rev-parse --show-toplevel)/.terraform-docs.yml" .'
     Manually updating sections between TF_DOCS tags may be overwritten.
     See https://terraform-docs.io/user-guide/configuration/ for more information.
-->
## Outputs

| Name | Description |
|------|-------------|
| <a name="output_codebuild_project_arn"></a> [codebuild\_project\_arn](#output\_codebuild\_project\_arn) | ARN of the CodeBuild project |
| <a name="output_codebuild_project_name"></a> [codebuild\_project\_name](#output\_codebuild\_project\_name) | Name of the CodeBuild project |
| <a name="output_codebuild_role_arn"></a> [codebuild\_role\_arn](#output\_codebuild\_role\_arn) | ARN of the CodeBuild service role |
| <a name="output_ecr_kms_key_arn"></a> [ecr\_kms\_key\_arn](#output\_ecr\_kms\_key\_arn) | ARN of the KMS key used for ECR encryption |
| <a name="output_ecr_repository_arn"></a> [ecr\_repository\_arn](#output\_ecr\_repository\_arn) | ARN of the ECR repository |
| <a name="output_ecr_repository_url"></a> [ecr\_repository\_url](#output\_ecr\_repository\_url) | URL of the ECR repository |
| <a name="output_env_kms_key_alias"></a> [env\_kms\_key\_alias](#output\_env\_kms\_key\_alias) | Alias of the environment KMS key |
| <a name="output_env_kms_key_arn"></a> [env\_kms\_key\_arn](#output\_env\_kms\_key\_arn) | ARN of the environment KMS key |
| <a name="output_github_actions_role_arn"></a> [github\_actions\_role\_arn](#output\_github\_actions\_role\_arn) | ARN of GitHub Actions deployment role |
| <a name="output_github_actions_role_name"></a> [github\_actions\_role\_name](#output\_github\_actions\_role\_name) | Name of GitHub Actions deployment role |
| <a name="output_github_connection_arn"></a> [github\_connection\_arn](#output\_github\_connection\_arn) | ARN of the GitHub CodeStar connection |
| <a name="output_github_oidc_provider_arn"></a> [github\_oidc\_provider\_arn](#output\_github\_oidc\_provider\_arn) | ARN of GitHub Actions OIDC provider |
<!-- END_TF_DOCS -->