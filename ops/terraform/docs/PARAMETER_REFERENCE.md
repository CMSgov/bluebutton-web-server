# SSM Parameter Hierarchy: Blue Button API

## Overview

This document describes the AWS Systems Manager (SSM) Parameter Store hierarchy used for Blue Button deployment configuration.

---

## Hierarchy Structure

```
/bluebutton/
├── {env}/
│   ├── common/                    # Shared configuration across components
│   │   ├── app
│   │   ├── vpc_id
│   │   ├── azs                    # JSON array: ["us-east-1a", "us-east-1b", "us-east-1c"]
│   │   └── ci_cidrs               # JSON array: ["10.x.x.x", ...]
│   │
│   └── config/                    # Environment-specific configuration
│       │
│       │  # Core Configuration
│       ├── stack
│       ├── env
│       ├── acm_domain             # Specific domain for search (e.g. test.bluebutton.cms.gov)
│       ├── app_config_bucket
│       ├── static_content_bucket
│       │
│       │  # API Service Configuration (Fargate)
│       ├── api_cpu                # CPU units (256, 512, 1024, 2048, 4096)
│       ├── api_memory             # Memory in MB (512, 1024, 2048, etc.)
│       ├── api_count              # Desired number of tasks
│       ├── api_min_capacity       # Minimum tasks for auto scaling
│       ├── api_max_capacity       # Maximum tasks for auto scaling
│       ├── api_port               # Container port (default: 8000)
│       ├── health_check_path      # Health check endpoint (default: /health)
│       └── ecr_repository_url     # ECR repository URL
```

## Environments

- `test` - Test environment
- `sandbox` - Sandbox environment  
- `prod` - Production environment

---

## API Service Parameters (Fargate)

### Required Configuration

| Parameter | Config Key | Type | Required |
|-----------|------------|------|----------|
| `api_cpu` | `module.platform.config.api_cpu` | Number | ✅ |
| `api_memory` | `module.platform.config.api_memory` | Number | ✅ |
| `api_count` | `module.platform.config.api_count` | Number | ✅ |
| `api_min_capacity` | `module.platform.config.api_min_capacity` | Number | ✅ |
| `api_max_capacity` | `module.platform.config.api_max_capacity` | Number | ✅ |
| `api_port` | `module.platform.config.api_port` | Number | ✅ |
| `api_health_check_path` | `module.platform.config.api_health_check_path` | String | ✅ |
| `api_alb` | `module.platform.config.api_alb` | Boolean | ✅ |
| `api_autoscale_enabled` | `module.platform.config.api_autoscale_enabled` | Boolean | ✅ |
| `app_config_bucket` | `module.platform.config.app_config_bucket` | String | Optional |
| `static_content_bucket` | `module.platform.config.static_content_bucket` | String | Optional |

> [!WARNING]
> **All parameters are now REQUIRED** (no defaults). Terraform will fail if any required parameter is missing from SSM.

> [!IMPORTANT]
> **HTTPS Only**: All traffic is routed over port 443. Target groups and container health checks must use the HTTPS protocol.

### Accessing in Terraform

```hcl
# Simplified access via platform.config
port   = module.platform.config.api_port
cpu    = module.platform.config.api_cpu
memory = module.platform.config.api_memory
```

### Setting Parameters

```bash
export ENV=test  # or sandbox, prod

aws ssm put-parameter --name "/bluebutton/${ENV}/config/api_cpu" --value "512" --type String --overwrite
aws ssm put-parameter --name "/bluebutton/${ENV}/config/api_memory" --value "1024" --type String --overwrite
aws ssm put-parameter --name "/bluebutton/${ENV}/config/api_count" --value "2" --type String --overwrite
aws ssm put-parameter --name "/bluebutton/${ENV}/config/api_min_capacity" --value "1" --type String --overwrite
aws ssm put-parameter --name "/bluebutton/${ENV}/config/api_max_capacity" --value "4" --type String --overwrite
aws ssm put-parameter --name "/bluebutton/${ENV}/config/api_port" --value "8000" --type String --overwrite
aws ssm put-parameter --name "/bluebutton/${ENV}/config/api_health_check_path" --value "/health" --type String --overwrite
aws ssm put-parameter --name "/bluebutton/${ENV}/config/api_alb" --value "true" --type String --overwrite
aws ssm put-parameter --name "/bluebutton/${ENV}/config/api_autoscale_enabled" --value "true" --type String --overwrite
```

---

## Secrets Manager

Application secrets are stored in **AWS Secrets Manager** and auto-discovered at runtime.

### Secret Path Pattern
```
/bb2/{env}/app/*
```

**Examples:**
- `/bb2/test/app/database-url` → Injected as `DATABASE_URL`
- `/bb2/test/app/api-key` → Injected as `API_KEY`
- `/bb2/prod/app/db-user-pw` → Injected as `DB_USER_PW`

### Auto-Discovery
The ECS module automatically:
1. Discovers all secrets under `/bb2/{env}/app/*`
2. Converts names to uppercase environment variables
3. Replaces hyphens with underscores
4. Injects them into ECS task definitions

> [!NOTE]
> Secrets are injected at **runtime** via ECS task definition `secrets` blocks, not stored in Terraform state.

---

## Parameter Types

### String Parameters
- `app`, `stack`, `env`, `vpc_id`
- Security group IDs, bucket names, domain names
- API configuration values

### SecureString Parameters (KMS encrypted)
- Any parameter containing "key", "secret", or "password"

### JSON-Encoded Parameters
```
azs: ["us-east-1a", "us-east-1b", "us-east-1c"]
ci_cidrs: ["10.x.x.x/32", "10.x.x.0/32"]
```

---

## Documentation Links

- **[SSM Configuration Guide](../SSM_CONFIGURATION_GUIDE.md)** - Main pattern and setup guide
- **[Architecture Overview](ARCHITECTURE.md)** - Infrastructure diagram and modules
- **[CodeBuild Setup](CODEBUILD_SETUP.md)** - GitHub Actions integration

