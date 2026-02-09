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

# Initialize
tofu init -var="parent_env=prod"

# Plan
tofu plan -var="parent_env=prod"

# Apply
tofu apply -var="parent_env=prod"
```

## Outputs

Key outputs for downstream services:

- `cluster_id` - ECS cluster identifier
- `cluster_arn` - Full cluster ARN for IAM policies
- `cluster_name` - Human-readable cluster name
- `capacity_providers` - List of available capacity providers

## Usage by Other Services

Services reference this cluster via remote state:

```hcl
data "terraform_remote_state" "cluster" {
  backend = "s3"
  config = {
    bucket = "bb-${local.env}-app-config"
    key    = "ops/services/cluster/tofu.tfstate"
    region = "us-east-1"
  }
}

resource "aws_ecs_service" "example" {
  cluster = data.terraform_remote_state.cluster.outputs.cluster_arn
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
3. **Capacity Providers** - Use FARGATE for production, FARGATE_SPOT for dev/test
4. **Tagging** - Consistent tags for cost allocation
