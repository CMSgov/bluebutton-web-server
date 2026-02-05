# Blue Button API Server - ECS Fargate Deployment

OpenTofu configuration for deploying Blue Button API server on AWS ECS Fargate following the **Terraservice** pattern.

## Architecture
- **[Architecture Overview & Diagram](../docs/ARCHITECTURE.md)**
- **[CodeBuild Setup Guide](../docs/CODEBUILD_SETUP.md)**
- **[SSM Parameter Reference](../docs/PARAMETER_REFERENCE.md)**

## Quick Start

### 1. Configure Environment (SSM)

Set parameters in AWS SSM Parameter Store:

```bash
export ENV=test  # or sandbox, prod

# API Sizing
aws ssm put-parameter --name "/bluebutton/${ENV}/config/api_cpu" --value "512" --type String --overwrite
aws ssm put-parameter --name "/bluebutton/${ENV}/config/api_memory" --value "1024" --type String --overwrite
aws ssm put-parameter --name "/bluebutton/${ENV}/config/api_port" --value "8000" --type String --overwrite
```

### 2. Deploy

```bash
cd ops/terraform/services

# Initialize
tofu init

# Select environment workspace
tofu workspace select test || tofu workspace new test

# Plan and Apply
tofu plan -out=plan.out
tofu apply plan.out
```

### 3. Confirm CodeStar Connection

After first deployment, authorize the GitHub connection:
1. AWS Console → Developer Tools → Settings → Connections
2. Find `bb-github-connection` → Update pending connection
3. Authorize with GitHub

## Module Architecture

| Module | Description |
|--------|-------------|
| `bb-platform` | Environment discovery, VPC, subnets, ACM, SSM loading, typed config |
| `bb-ecs` | ECS cluster, ALB, API service, Auto Scaling, Security Groups |
| `bb-codebuild` | CodeBuild runner, ECR repository, GitHub OIDC |

## Configuration Access

Configuration is loaded from SSM via `module.platform.config`:

```hcl
port   = module.platform.config.api_port         # Default: 8000
cpu    = module.platform.config.api_cpu          # Default: 512
memory = module.platform.config.api_memory       # Default: 1024
```

## Security Groups

| Security Group | Purpose |
|----------------|---------|
| `cmscloud-vpn` | CMS VPN access |
| `bb-sg-{env}-clb-cms-vpn` | Environment-specific VPN |
| `bb-sg-{env}-clb-akamai-prod` | Akamai CDN traffic |
| `bb-{env}-api-alb-sg` | ALB ingress |
| `bb-{env}-ecs-api-sg` | ECS ingress (from ALB only) |

## Outputs

```bash
tofu output ecs_cluster_name
tofu output alb_dns_names
tofu output codebuild_project_name
tofu output github_actions_role_arn
```

## Deployment Commands

| Command | Description |
|---------|-------------|
| `tofu init` | Initialize providers |
| `tofu plan` | Preview changes |
| `tofu apply` | Deploy |
| `tofu workspace select <env>` | Switch environment |

## Logs & Monitoring

- **ECS Logs**: `/aws/ecs/fargate/bb-{env}-api-service`
- **CodeBuild Logs**: `/aws/codebuild/bb-{env}-web-server`
- **Health**: `https://<api-domain>/health`

