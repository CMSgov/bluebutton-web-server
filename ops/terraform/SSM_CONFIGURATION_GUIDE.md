# SSM Configuration Guide: Blue Button API

This guide describes how to manage infrastructure configuration using AWS Systems Manager (SSM) Parameter Store.

## Configuration Pattern

Following the **Terraservice pattern**, configuration is centralized in the `bb-platform` module and consumed by application modules:

```
SSM Parameter Store
    ↓
bb-platform module (loads SSM → platform.config)
    ↓
bb-ecs / bb-codebuild modules (use platform.config values)
```

---

## Accessing Configuration in Terraform

Configuration values are exposed via `module.platform.config`:

```hcl
# Simplified access with typed defaults
port   = module.platform.config.api_port          # 8000
cpu    = module.platform.config.api_cpu           # 512
memory = module.platform.config.api_memory        # 1024

# Raw SSM access (if needed)
value = module.platform.ssm["/bluebutton/config/custom_param"]
```

---

## Setup Steps

### 1. Populate SSM for Your Environment

```bash
export ENV=test  # or sandbox, prod

# Base Networking (usually pre-configured)
aws ssm put-parameter --name "/bluebutton/${ENV}/common/vpc_id" --value "vpc-xxxxxx" --type String --overwrite

# API Sizing & Capacity
aws ssm put-parameter --name "/bluebutton/${ENV}/config/api_cpu" --value "512" --type String --overwrite
aws ssm put-parameter --name "/bluebutton/${ENV}/config/api_memory" --value "1024" --type String --overwrite
aws ssm put-parameter --name "/bluebutton/${ENV}/config/api_port" --value "8000" --type String --overwrite
```

### 2. Deploy

```bash
cd ops/terraform/services
tofu init
tofu workspace select test || tofu workspace new test
tofu plan -out=plan.out
tofu apply plan.out
```

---

## Available Config Values

| Config Key | Default | SSM Path |
|------------|---------|----------|
| `api_port` | 8000 | `/bluebutton/{env}/config/api_port` |
| `api_cpu` | 512 | `/bluebutton/{env}/config/api_cpu` |
| `api_memory` | 1024 | `/bluebutton/{env}/config/api_memory` |
| `api_count` | 2 | `/bluebutton/{env}/config/api_count` |
| `api_min_capacity` | 1 | `/bluebutton/{env}/config/api_min_capacity` |
| `api_max_capacity` | 4 | `/bluebutton/{env}/config/api_max_capacity` |
| `api_health_check_path` | /health | `/bluebutton/{env}/config/api_health_check_path` |
| `app_config_bucket` | "" | `/bluebutton/{env}/config/app_config_bucket` |
| `static_content_bucket` | "" | `/bluebutton/{env}/config/static_content_bucket` |

---

## Common Operations

### View Current Configuration
```bash
aws ssm get-parameters-by-path --path "/bluebutton/test/" --recursive --with-decryption
```

### Update a Parameter
```bash
aws ssm put-parameter --name "/bluebutton/test/config/api_count" --value "4" --overwrite
```

---

## Documentation Links

- **[Architecture Overview](docs/ARCHITECTURE.md)** - Visual diagram and module details
- **[Parameter Reference](docs/PARAMETER_REFERENCE.md)** - Full parameter list
- **[CodeBuild Setup](docs/CODEBUILD_SETUP.md)** - GitHub Actions integration

