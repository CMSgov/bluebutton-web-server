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
- `impl` - Implementation/Sandbox environment  
- `prod` - Production environment

---

## API Service Parameters (Fargate)

### Required Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_cpu` | Number | 512 | CPU units (512=0.5 vCPU) |
| `api_memory` | Number | 1024 | Memory in MB |
| `api_count` | Number | 2 | Desired task count |
| `api_min_capacity` | Number | 1 | Min tasks (auto scaling) |
| `api_max_capacity` | Number | 4 | Max tasks (auto scaling) |
| `api_port` | Number | 8000 | Container port |
| `health_check_path` | String | /health | Health check endpoint |

> [!IMPORTANT]
> **HTTPS Only**: All traffic is routed over port 443. Target groups and container health checks must use the HTTPS protocol.

### Setting Parameters

```bash
# Set API parameters for test environment
aws ssm put-parameter --name "/bluebutton/test/config/api_cpu" --value "512" --type String --overwrite
aws ssm put-parameter --name "/bluebutton/test/config/api_memory" --value "1024" --type String --overwrite
aws ssm put-parameter --name "/bluebutton/test/config/api_count" --value "2" --type String --overwrite
aws ssm put-parameter --name "/bluebutton/test/config/api_port" --value "8000" --type String --overwrite
aws ssm put-parameter --name "/bluebutton/test/config/health_check_path" --value "/health" --type String --overwrite
```

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
ci_cidrs: ["10.244.136.0/23", "10.252.51.0/24"]
```

---

## Documentation Links

- **[SSM Configuration Guide](../SSM_CONFIGURATION_GUIDE.md)** - Main pattern and setup guide
- **[Deployment Walkthrough](../../.gemini/antigravity/brain/16b5c778-ca10-4247-be69-f67816fcc73b/walkthrough.md)** - Step-by-step deploy guide
