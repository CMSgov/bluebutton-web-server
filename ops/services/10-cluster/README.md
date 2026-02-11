# Cluster Service

## Overview

Creates and manages the ECS Fargate cluster used by all application services. This cluster is shared across all services in the environment.

## Resources Managed

### Compute Platform
- **ECS Cluster**: Fargate-based container orchestration
- **Capacity Providers**: FARGATE and FARGATE_SPOT configurations
- **Container Insights**: CloudWatch Container Insights enabled

## Architecture

```
┌─────────────────────────────────────────┐
│         10-cluster                      │
├─────────────────────────────────────────┤
│                                          │
│  ECS Cluster                             │
│  ├─ FARGATE (base capacity)             │
│  └─ FARGATE_SPOT (cost optimization)    │
│                                          │
└─────────────────────────────────────────┘
         ▲
         │
  Used by 20-microservices
```

## Capacity Provider Strategy

**FARGATE:**
- Base: 1 (minimum number of tasks)
- Weight: 100 (preferred for reliability)

**FARGATE_SPOT:**
- Base: 0
- Weight: 0 (available but not default)
- Services can opt-in for cost savings

## Container Insights

Enabled by default, providing:
- CPU and memory utilization metrics
- Network performance metrics
- Task and container-level metrics
- CloudWatch dashboard integration

## Dependencies

**Upstream:**
- `00-bootstrap` - Platform infrastructure

**Downstream:**
- `20-microservices` - ECS services use this cluster

## Initialization

```bash
cd ops/services/10-cluster

# Initialize (parent_env determines S3 bucket for state)
tofu init -var="parent_env=test"

# Select workspace
tofu workspace select test

# Plan and apply
tofu plan
tofu apply
```

## Outputs

Key outputs for downstream services:

- `cluster_id` - ECS cluster identifier
- `cluster_arn` - Full cluster ARN for IAM policies
- `cluster_name` - Human-readable cluster name
- `capacity_providers` - List of available capacity providers

## Usage by Other Services

Downstream services discover this cluster via AWS data sources (not remote state):

```hcl
data "aws_ecs_cluster" "main" {
  cluster_name = "bb-${local.workspace}-cluster"
}

resource "aws_ecs_service" "example" {
  cluster = data.aws_ecs_cluster.main.arn
  # ...
}
```

## Cost Optimization

### Fargate Spot
Services can use Fargate Spot for non-critical workloads:

```hcl
capacity_provider_strategy {
  capacity_provider = "FARGATE_SPOT"
  weight            = 100
  base              = 0
}
```

**Savings:** Up to 70% compared to regular Fargate

**Tradeoffs:** 
- Tasks may be interrupted with 2-minute warning
- Best for stateless, fault-tolerant workloads

## Monitoring

Container Insights metrics available in CloudWatch:
- **Namespace:** `ECS/ContainerInsights`
- **Dimensions:** `ClusterName`, `ServiceName`, `TaskDefinitionFamily`

## Best Practices

1. **One Cluster Per Environment** - test, sandbox, prod each have their own
2. **Container Insights** - Always enabled for observability
3. **Capacity Providers** - Use FARGATE for production, FARGATE_SPOT for test/non-critical
4. **Tagging** - Consistent tags for cost allocation

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

<!--WARNING: GENERATED CONTENT with terraform-docs, e.g.
     'terraform-docs --config "$(git rev-parse --show-toplevel)/.terraform-docs.yml" .'
     Manually updating sections between TF_DOCS tags may be overwritten.
     See https://terraform-docs.io/user-guide/configuration/ for more information.
-->
## Resources

| Name | Type |
|------|------|
| [aws_cloudwatch_log_group.cluster](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) | resource |
| [aws_ecs_cluster.main](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_cluster) | resource |
| [aws_ecs_cluster_capacity_providers.main](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_cluster_capacity_providers) | resource |

<!--WARNING: GENERATED CONTENT with terraform-docs, e.g.
     'terraform-docs --config "$(git rev-parse --show-toplevel)/.terraform-docs.yml" .'
     Manually updating sections between TF_DOCS tags may be overwritten.
     See https://terraform-docs.io/user-guide/configuration/ for more information.
-->
## Outputs

| Name | Description |
|------|-------------|
| <a name="output_capacity_providers"></a> [capacity\_providers](#output\_capacity\_providers) | Capacity providers configured for the cluster |
| <a name="output_cluster_arn"></a> [cluster\_arn](#output\_cluster\_arn) | ARN of the ECS cluster |
| <a name="output_cluster_id"></a> [cluster\_id](#output\_cluster\_id) | ID of the ECS cluster |
| <a name="output_cluster_name"></a> [cluster\_name](#output\_cluster\_name) | Name of the ECS cluster |
<!-- END_TF_DOCS -->