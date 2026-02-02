# Blue Button API Server - ECS Fargate Deployment

OpenTofu configuration for deploying Blue Button API server on AWS ECS Fargate following the **Terraservice** pattern.

## Architecture
- **[Architecture Overview & Diagram](docs/ARCHITECTURE.md)**

## Quick Start

### 1. Build and Push Container Image

```bash
# 1. Get ECR URL from OpenTofu output
ECR_URL=$(tofu output -json ecr_repository_urls | jq -r '.api')

# 2. Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin ${ECR_URL}

# 3. Build image
docker build -f Dockerfile.prod -t bb-api-server .

# 4. Tag and push
docker tag bb-api-server:latest ${ECR_URL}:latest
docker push ${ECR_URL}:latest
```

### 2. Configure Environment (SSM)

Set the following parameters in AWS SSM Parameter Store:

```bash
# Sizing for API tasks
aws ssm put-parameter --name "/bluebutton/test/config/api_cpu" --value "512" --type String --overwrite
aws ssm put-parameter --name "/bluebutton/test/config/api_memory" --value "1024" --type String --overwrite
aws ssm put-parameter --name "/bluebutton/test/config/api_count" --value "2" --type String --overwrite
```

### 3. Deploy

```bash
cd ops/terraform/services

# Initialize
tofu init

# Select environment workspace
tofu workspace select test || tofu workspace new test

# Plan and Apply
tofu plan
tofu apply
```

## Module Architecture

| Module | Description |
|--------|-------------|
| `bb-platform` | Environment discovery, VPC, subnets, ACM, SSM loading |
| `bb-ecs` | ECS cluster, ALB (HTTPS only), API service, Auto Scaling |

## Configuration (SSM)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `/bluebutton/{env}/config/api_cpu` | 512 | CPU units (512 = 0.5 vCPU) |
| `/bluebutton/{env}/config/api_memory` | 1024 | Memory in MB |
| `/bluebutton/{env}/config/api_count` | 2 | Desired task count |
| `/bluebutton/{env}/config/api_min_capacity` | 1 | Auto-scaling minimum |
| `/bluebutton/{env}/config/api_max_capacity` | 4 | Auto-scaling maximum |
| `/bluebutton/{env}/config/api_port` | 8000 | Container port (internal) |

> [!IMPORTANT]
> **HTTPS Standard**: This infrastructure is **HTTPS-only** (Port 443). Internal communication between the ALB and API tasks is also encrypted via HTTPS.

## Deployment Commands

- **Initialize**: `tofu init`
- **Plan**: `tofu plan`
- **Apply**: `tofu apply`
- **Switch Env**: `tofu workspace select <env>`
- **Force Update**: `aws ecs update-service --cluster bb-<env> --service bb-<env>-api-service --force-new-deployment`

## Logs & Monitoring

- **Logs**: CloudWatch Logs at `/aws/ecs/fargate/bb-<env>-api-service`
- **Metrics**: CloudWatch Container Insights on the `bb-<env>` cluster
- **Health**: Check ALB endpoint via `https://<api-domain>/health`
