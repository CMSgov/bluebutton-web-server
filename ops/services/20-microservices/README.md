# Microservices Layer

## Overview

ECS Fargate application layer that runs the Blue Button API services, with ALB, auto-scaling, IAM, and secrets management.

## Resources Managed

- **ECS Services & Task Definitions** — Fargate containers per service in `backend_services`
- **Application Load Balancer** — Public HTTPS endpoint with TLS 1.3
- **Target Groups** — HTTP health-checked backend routing
- **Security Groups** — ALB (443 inbound) and ECS (ALB-only inbound)
- **CloudWatch Log Groups** — Per-service container logs
- **Auto-scaling** — CPU/memory target tracking policies
- **IAM Roles** — Execution role (ECR, logs, secrets) and task role (SSM, KMS, S3)

## Architecture

```
Internet → ALB (HTTPS:443) → Target Group (HTTP) → ECS Service (Fargate, port 8000)
                                                         ↓
                                                   Secrets Manager (/bb2/{env}/app/*)
                                                   SSM Parameters  (/bb/{env}/*/config)
```

## Configuration

### Priority Order

1. **`var.service_overrides`** — Terraform variable (for testing/emergency)
2. **SSM JSON parameter** — `/bb/{env}/{service}/config` (single JSON per service)
3. **Hardcoded defaults** — cpu=512, memory=1024, port=8000, count=1

### SSM JSON Config

Path: `/bb/{env}/{service}/config`

```json
{
  "port": 8000,
  "cpu": 512,
  "memory": 1024,
  "count": 1,
  "scaling_min": 1,
  "scaling_max": 2,
  "health_check_path": "/health",
  "alb_enabled": true,
  "autoscale_enabled": false
}
```

Set `enable_ssm_config = false` to skip SSM lookup and use defaults only.

### Service Overrides (Optional)

```hcl
service_overrides = {
  api = {
    cpu          = 1024
    memory       = 2048
    count        = 3
    min_capacity = 2
    max_capacity = 10
  }
}
```

## Secrets

### Auto-Discovery
All secrets under `/bb2/{env}/app/` in Secrets Manager are automatically discovered and injected as container environment variables.

**Name mapping:** `/bb2/test/app/database_password` becomes `DATABASE_PASSWORD`

### Excluded Secrets
Infrastructure-only secrets are filtered out:
`ssh_users`, `mon_nessus_*`, `tfbackend*`, `www_combined_crt`, `www_key_file`, `cf_app_pyapps_pwd`

### Default Environment Variables
Set in `locals.tf` (not from secrets):
- `TARGET_ENV`, `ENVIRONMENT` — workspace name
- `PORT` — 8000
- `DJANGO_FHIR_CERTSTORE`, `FHIR_CERT_FILE`, `FHIR_KEY_FILE` — cert paths
- `PYTHONUNBUFFERED`, `PYTHONDONTWRITEBYTECODE`
- `NEW_RELIC_*` — APM configuration

## Cross-Service Discovery

Uses AWS data sources (not `terraform_remote_state`):

```hcl
# ECS Cluster (from 10-cluster)
data "aws_ecs_cluster" "main" {
  cluster_name = "bb-${local.workspace}-cluster"
}

# ECR Repository (from 00-bootstrap)
data "aws_ecr_repository" "api" {
  name = "bb-${local.bucket_env}-api"
}
```

## Dependencies

| Upstream | What it provides |
|----------|-----------------|
| `00-bootstrap` | ECR repository |
| `01-config` | SSM parameters (from SOPS) |
| `10-cluster` | ECS Cluster |

## Deployment

```bash
cd ops/services/20-microservices

tofu init -var="parent_env=test"
tofu workspace select test
tofu plan
tofu apply
```

## IAM

### Execution Role (ECS Agent)
- `AmazonECSTaskExecutionRolePolicy` (ECR pull, CloudWatch write)
- Secrets Manager access: `/bb2/{env}/*`, `/bb/{env}/*`
- SSM access: `/bb/{env}/*`
- KMS decrypt

### Task Role (Container Runtime)
- Secrets Manager, SSM, KMS (same as execution)
- S3 access: `bb-{env}-app-config`, `bb-{env}-static-content`

## Outputs

| Output | Description |
|--------|-------------|
| `service_names` | Map of ECS service names |
| `alb_dns_names` | Map of ALB DNS names |
| `alb_zone_ids` | Map of ALB Route 53 zone IDs |
| `target_group_arns` | Map of target group ARNs |
| `ecs_security_group_ids` | Map of ECS security group IDs |
| `log_group_names` | Map of CloudWatch log group names |

## Troubleshooting

**Service won't start:**
- Check CloudWatch logs: `/bb/{env}/{service}`
- Verify secrets exist in Secrets Manager under `/bb2/{env}/app/`
- Confirm ECR image exists

**ALB health checks failing:**
- Health check uses HTTP (not HTTPS) on traffic-port
- Verify health check path returns HTTP 200
- Check security group allows ALB → ECS traffic

**SSM config not loading:**
- Verify JSON parameter exists at `/bb/{env}/{service}/config`
- Set `enable_ssm_config = false` to use defaults while debugging

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
| <a name="input_access_logs_bucket"></a> [access\_logs\_bucket](#input\_access\_logs\_bucket) | S3 bucket for ALB access logs | `string` | `""` | no |
| <a name="input_alarm_email"></a> [alarm\_email](#input\_alarm\_email) | Email address for CloudWatch alarm notifications (optional) | `string` | `""` | no |
| <a name="input_alb_allow_all_ingress"></a> [alb\_allow\_all\_ingress](#input\_alb\_allow\_all\_ingress) | Allow HTTPS from 0.0.0.0/0 when true, restrict to VPN/CDN security groups when false | `bool` | `false` | no |
| <a name="input_alb_security_group_ids"></a> [alb\_security\_group\_ids](#input\_alb\_security\_group\_ids) | Additional security group IDs to attach to ALB (VPN, Akamai, etc.) | `list(string)` | `[]` | no |
| <a name="input_app_config_bucket"></a> [app\_config\_bucket](#input\_app\_config\_bucket) | App config S3 bucket | `string` | `""` | no |
| <a name="input_backend_services"></a> [backend\_services](#input\_backend\_services) | Service names to configure (all values loaded from SSM) | `set(string)` | <pre>[<br/>  "api"<br/>]</pre> | no |
| <a name="input_cluster_name"></a> [cluster\_name](#input\_cluster\_name) | Existing cluster name (when create\_cluster = false) | `string` | `""` | no |
| <a name="input_cpu_target_value"></a> [cpu\_target\_value](#input\_cpu\_target\_value) | CPU target for auto scaling | `number` | `70` | no |
| <a name="input_create_cluster"></a> [create\_cluster](#input\_create\_cluster) | Create new ECS cluster or use existing | `bool` | `true` | no |
| <a name="input_enable_access_logs"></a> [enable\_access\_logs](#input\_enable\_access\_logs) | Enable ALB access logs | `bool` | `true` | no |
| <a name="input_enable_deletion_protection"></a> [enable\_deletion\_protection](#input\_enable\_deletion\_protection) | Enable ALB deletion protection | `bool` | `false` | no |
| <a name="input_enable_ssm_config"></a> [enable\_ssm\_config](#input\_enable\_ssm\_config) | Read service config from SSM (/bb/{env}/{service}/config). Set false to use defaults only. | `bool` | `true` | no |
| <a name="input_environment_variables"></a> [environment\_variables](#input\_environment\_variables) | Additional environment variables for Django (hostname, email, SLSx, etc.) | <pre>list(object({<br/>    name  = string<br/>    value = string<br/>  }))</pre> | `[]` | no |
| <a name="input_image_tag"></a> [image\_tag](#input\_image\_tag) | Container image tag | `string` | `"latest"` | no |
| <a name="input_log_retention_days"></a> [log\_retention\_days](#input\_log\_retention\_days) | CloudWatch log retention in days | `number` | `30` | no |
| <a name="input_memory_target_value"></a> [memory\_target\_value](#input\_memory\_target\_value) | Memory target for auto scaling | `number` | `80` | no |
| <a name="input_parent_env"></a> [parent\_env](#input\_parent\_env) | The parent environment of the current solution. Will correspond with `terraform.workspace`.<br/>Necessary on `tofu init` and `tofu workspace select` \_only\_. In all other situations, parent env<br/>will be divined from `terraform.workspace`. | `string` | `null` | no |
| <a name="input_region"></a> [region](#input\_region) | AWS region for resources | `string` | `"us-east-1"` | no |
| <a name="input_root_module"></a> [root\_module](#input\_root\_module) | Root module URL for tracking (e.g., GitHub URL) | `string` | `"https://github.com/CMSgov/bluebutton-web-server"` | no |
| <a name="input_secondary_region"></a> [secondary\_region](#input\_secondary\_region) | Secondary AWS region for DR/failover | `string` | `"us-west-2"` | no |
| <a name="input_secrets"></a> [secrets](#input\_secrets) | Secrets to inject from Secrets Manager | <pre>list(object({<br/>    name       = string<br/>    value_from = string<br/>  }))</pre> | `[]` | no |
| <a name="input_service_overrides"></a> [service\_overrides](#input\_service\_overrides) | Per-service configuration overrides (bypasses SSM for testing/emergency scenarios).<br/>All values are optional. If not provided, SSM values are used.<br/><br/>Example:<br/>  service\_overrides = {<br/>    api = {<br/>      cpu          = 1024<br/>      memory       = 2048<br/>      count        = 1<br/>      min\_capacity = 1<br/>      max\_capacity = 2<br/>    }<br/>  } | <pre>map(object({<br/>    cpu               = optional(number)<br/>    memory            = optional(number)<br/>    count             = optional(number)<br/>    min_capacity      = optional(number)<br/>    max_capacity      = optional(number)<br/>    health_check_path = optional(string)<br/>  }))</pre> | `{}` | no |
| <a name="input_static_content_bucket"></a> [static\_content\_bucket](#input\_static\_content\_bucket) | Static content S3 bucket | `string` | `""` | no |

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
| [aws_appautoscaling_policy.ecs_cpu_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/appautoscaling_policy) | resource |
| [aws_appautoscaling_policy.ecs_memory_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/appautoscaling_policy) | resource |
| [aws_appautoscaling_target.ecs_autoscale](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/appautoscaling_target) | resource |
| [aws_cloudwatch_log_group.ecs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) | resource |
| [aws_cloudwatch_metric_alarm.api_4xx_errors](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_metric_alarm) | resource |
| [aws_cloudwatch_metric_alarm.api_5xx_errors](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_metric_alarm) | resource |
| [aws_cloudwatch_metric_alarm.api_latency_p99](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_metric_alarm) | resource |
| [aws_cloudwatch_metric_alarm.elb_5xx_errors](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_metric_alarm) | resource |
| [aws_cloudwatch_metric_alarm.log_availability](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_metric_alarm) | resource |
| [aws_cloudwatch_metric_alarm.unhealthy_hosts](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_metric_alarm) | resource |
| [aws_ecs_service.ecs_service](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_service) | resource |
| [aws_ecs_task_definition.ecs_task](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_task_definition) | resource |
| [aws_iam_policy.kms](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) | resource |
| [aws_iam_policy.s3](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) | resource |
| [aws_iam_policy.secrets](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) | resource |
| [aws_iam_policy.ssm](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) | resource |
| [aws_iam_role.execution](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role.task](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role_policy_attachment.execution_base](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_role_policy_attachment.execution_kms](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_role_policy_attachment.execution_secrets](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_role_policy_attachment.execution_ssm](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_role_policy_attachment.task_kms](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_role_policy_attachment.task_s3](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_role_policy_attachment.task_secrets](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_role_policy_attachment.task_ssm](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_lb.alb](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb) | resource |
| [aws_lb_listener.https](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_listener) | resource |
| [aws_lb_target_group.tg](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb_target_group) | resource |
| [aws_security_group.alb_sg](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group) | resource |
| [aws_security_group.ecs_sg](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group) | resource |
| [aws_sns_topic.alarms](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic) | resource |
| [aws_sns_topic_subscription.alarms_email](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic_subscription) | resource |
| [aws_vpc_security_group_egress_rule.alb_all](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_security_group_egress_rule) | resource |
| [aws_vpc_security_group_egress_rule.ecs_all](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_security_group_egress_rule) | resource |
| [aws_vpc_security_group_ingress_rule.alb_from_additional](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_security_group_ingress_rule) | resource |
| [aws_vpc_security_group_ingress_rule.alb_from_akamai](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_security_group_ingress_rule) | resource |
| [aws_vpc_security_group_ingress_rule.alb_from_cms_vpn](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_security_group_ingress_rule) | resource |
| [aws_vpc_security_group_ingress_rule.alb_from_vpn](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_security_group_ingress_rule) | resource |
| [aws_vpc_security_group_ingress_rule.alb_https_open](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_security_group_ingress_rule) | resource |
| [aws_vpc_security_group_ingress_rule.ecs_from_alb](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_security_group_ingress_rule) | resource |
| [aws_vpc_security_group_ingress_rule.ecs_from_private](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_security_group_ingress_rule) | resource |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity) | data source |
| [aws_ecr_repository.api](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/ecr_repository) | data source |
| [aws_ecs_cluster.main](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/ecs_cluster) | data source |
| [aws_iam_policy_document.ecs_assume_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_policy_document.kms](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_policy_document.s3](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_policy_document.secrets](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_policy_document.ssm](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_region.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/region) | data source |
| [aws_secretsmanager_secret.app_secrets](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/secretsmanager_secret) | data source |
| [aws_secretsmanager_secrets.app_secrets](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/secretsmanager_secrets) | data source |
| [aws_security_group.clb_akamai](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/security_group) | data source |
| [aws_security_group.clb_cms_vpn](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/security_group) | data source |
| [aws_security_group.cmscloud_vpn](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/security_group) | data source |
| [aws_ssm_parameter.service_config](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/ssm_parameter) | data source |

<!--WARNING: GENERATED CONTENT with terraform-docs, e.g.
     'terraform-docs --config "$(git rev-parse --show-toplevel)/.terraform-docs.yml" .'
     Manually updating sections between TF_DOCS tags may be overwritten.
     See https://terraform-docs.io/user-guide/configuration/ for more information.
-->
## Outputs

| Name | Description |
|------|-------------|
| <a name="output_alb_dns_names"></a> [alb\_dns\_names](#output\_alb\_dns\_names) | ALB DNS names |
| <a name="output_alb_zone_ids"></a> [alb\_zone\_ids](#output\_alb\_zone\_ids) | ALB Route 53 zone IDs |
| <a name="output_cluster_arn"></a> [cluster\_arn](#output\_cluster\_arn) | ECS cluster ARN |
| <a name="output_cluster_name"></a> [cluster\_name](#output\_cluster\_name) | ECS cluster name |
| <a name="output_ecr_repository_url"></a> [ecr\_repository\_url](#output\_ecr\_repository\_url) | ECR repository URL from bootstrap |
| <a name="output_ecs_security_group_ids"></a> [ecs\_security\_group\_ids](#output\_ecs\_security\_group\_ids) | ECS task security group IDs |
| <a name="output_log_group_names"></a> [log\_group\_names](#output\_log\_group\_names) | CloudWatch log group names |
| <a name="output_service_names"></a> [service\_names](#output\_service\_names) | ECS service names |
| <a name="output_ssm_service_configs"></a> [ssm\_service\_configs](#output\_ssm\_service\_configs) | Parsed service configuration from SSM JSON |
| <a name="output_target_group_arns"></a> [target\_group\_arns](#output\_target\_group\_arns) | Target group ARNs |
<!-- END_TF_DOCS -->