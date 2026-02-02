# SSM Configuration Guide: Blue Button API

This guide describes how to manage infrastructure configuration using AWS Systems Manager (SSM) Parameter Store.

## Configuration Pattern

Following the **Terraservice pattern**, configuration is centralized in the `bb-platform` module and consumed by `bb-ecs`:

```
SSM Parameter Store
    ↓
bb-platform module (loads SSM into a platform object)
    ↓
bb-ecs module (builds infrastructure using the platform object)
```

---

## Setup Steps

### 1. Populate SSM for Your Environment

Before deploying, ensure the mandatory parameters are set in the `/bluebutton/{env}/` hierarchy.

```bash
export ENV=test  # or impl, prod

# Base Networking
aws ssm put-parameter --name "/bluebutton/${ENV}/common/vpc_id" --value "vpc-xxxxxx" --type String --overwrite

# API Sizing & Capacity
aws ssm put-parameter --name "/bluebutton/${ENV}/config/api_cpu" --value "512" --type String --overwrite
aws ssm put-parameter --name "/bluebutton/${ENV}/config/api_memory" --value "1024" --type String --overwrite
aws ssm put-parameter --name "/bluebutton/${ENV}/config/api_count" --value "2" --type String --overwrite
```

### 2. Initialize and Deploy

Navigate to the services directory and use OpenTofu workspaces to manage your environment context.

```bash
cd ops/terraform/services

# Initialize OpenTofu
tofu init

# Select/Create your environment workspace
tofu workspace select test || tofu workspace new test

# Plan and Apply
tofu plan
tofu apply
```

---

## Key Benefits

✅ **Centralized Strategy** - Single source of truth in SSM Parameter Store.  
✅ **Environment Parity** - Identical module calls across all environments.  
✅ **Secure by Default** - Encryption handled via KMS for sensitive values.  
✅ **HTTPS Mandatory** - End-to-end encryption enforced at all layers.

---

## Common Operations

### View Current Configuration
```bash
aws ssm get-parameters-by-path \
  --path "/bluebutton/test/" \
  --recursive \
  --with-decryption
```

### Update a Parameter
```bash
aws ssm put-parameter \
  --name "/bluebutton/test/config/api_count" \
  --value "4" \
  --overwrite
```

---

## Documentation Links

- **[Architecture Overview](docs/ARCHITECTURE.md)** - Visual diagram and pattern details
- **[Parameter Reference](docs/PARAMETER_REFERENCE.md)** - Full list of available parameters
- **[Deployment walkthrough](../../.gemini/antigravity/brain/16b5c778-ca10-4247-be69-f67816fcc73b/walkthrough.md)** - Complete deployment steps
