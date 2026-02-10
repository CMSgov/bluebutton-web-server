# BB2 Services Runbook

## Prerequisites

- **OpenTofu** >= 1.8 (check with `tofu version`)
- **AWS credentials** configured for the target account
- **S3 state buckets** exist: `bb-test-app-config`, `bb-prod-app-config`

## Environments

| Workspace | Account | Init Command |
|-----------|---------|-------------|
| `test` | Test | `tofu init -var="parent_env=test"` |
| `sandbox` | Prod | `tofu init -var="parent_env=prod"` |
| `prod` | Prod | `tofu init -var="parent_env=prod"` |

## Service Dependency Order

```
00-bootstrap    Foundation (ECR, KMS, CodeBuild, OIDC)
     |
01-config       Configuration (SOPS -> SSM parameters)
     |
10-cluster      ECS Fargate Cluster
     |
20-microservices  ECS Services, ALB, IAM, Auto-scaling
```

Always deploy top-to-bottom. Destroy bottom-to-top.

---

## First-Time Setup (New Environment)

### 1. Initialize and Deploy Bootstrap

```bash
cd ops/services/00-bootstrap

# Initialize backend (creates .terraform/)
tofu init -var="parent_env=test"

# Create workspace (first time only)
tofu workspace new test

# Review changes
tofu plan

# Apply
tofu apply
```

**Post-deploy:** Confirm GitHub CodeStar connection in AWS Console.

### 2. Deploy Config (SOPS)

```bash
cd ops/services/01-config

tofu init -var="parent_env=test"
tofu workspace new test

# First time: create encrypted values file from seed
cp values/test.sopsw.yaml.seed values/test.sopsw.yaml
# Edit with actual values, then encrypt:
bin/sopsw -e values/test.sopsw.yaml

tofu plan
tofu apply
```

### 3. Deploy Cluster

```bash
cd ops/services/10-cluster

tofu init -var="parent_env=test"
tofu workspace new test
tofu plan
tofu apply
```

### 4. Deploy Microservices

```bash
cd ops/services/20-microservices

tofu init -var="parent_env=test"
tofu workspace new test
tofu plan
tofu apply
```

---

## Day-to-Day Operations

### Plan a Single Service

```bash
cd ops/services/20-microservices
tofu workspace select test
tofu plan
```

### Apply a Single Service

```bash
cd ops/services/20-microservices
tofu workspace select test
tofu apply
```

### Plan All Services (Read-Only Check)

```bash
cd ops/services
for dir in 00-bootstrap 01-config 10-cluster 20-microservices; do
  echo "=== Planning $dir ==="
  (cd $dir && tofu workspace select test && tofu plan -detailed-exitcode) || true
  echo ""
done
```

### Deploy All Services

```bash
cd ops/services
for dir in 00-bootstrap 01-config 10-cluster 20-microservices; do
  echo "=== Deploying $dir ==="
  (cd $dir && tofu workspace select test && tofu apply -auto-approve)
  echo ""
done
```

### Validate All Services (No AWS Calls)

```bash
cd ops/services
for dir in 00-bootstrap 01-config 10-cluster 20-microservices; do
  echo "=== Validating $dir ==="
  (cd $dir && tofu validate)
done
```

---

## Switching Environments

The workspace determines which environment you operate on. The `parent_env` is only needed during `init` (to select the S3 bucket).

```bash
# Switch to prod
cd ops/services/20-microservices
tofu workspace select prod

# If workspace doesn't exist yet
tofu workspace new prod

# Plan against prod
tofu plan
```

**If switching between accounts** (test <-> prod), re-initialize:

```bash
# Switching from test to prod account
tofu init -reconfigure -var="parent_env=prod"
tofu workspace select prod
tofu plan
```

---

## Editing SOPS Config

```bash
cd ops/services/01-config

# Edit encrypted values for test
bin/sopsw -e values/test.sopsw.yaml

# Preview what SSM parameters will change
tofu plan

# Apply SSM parameter changes
tofu apply
```

---

## Deploying a New Container Image

Update the image tag and redeploy microservices:

```bash
cd ops/services/20-microservices
tofu workspace select test

# Deploy with a specific image tag
tofu apply -var="image_tag=v1.2.3"
```

---

## Checking State

### View Current State

```bash
cd ops/services/20-microservices
tofu workspace select test
tofu show
```

### List State Resources

```bash
tofu state list
```

### View Outputs

```bash
tofu output

# View a sensitive output
tofu output -raw alb_dns_names
```

### Check Which Workspace Is Active

```bash
tofu workspace show
```

---

## Troubleshooting

### "Backend configuration changed"

Re-initialize with the correct parent_env:

```bash
tofu init -reconfigure -var="parent_env=test"
```

### "Error acquiring the state lock"

A previous apply may have failed mid-run:

```bash
# Check for stale lock
aws s3 ls s3://bb-test-app-config/ops/services/microservices/

# Remove stale lock (use with caution)
aws s3 rm s3://bb-test-app-config/ops/services/microservices/.tflock
```

### "Resource already exists"

Import the existing resource into state:

```bash
tofu import 'aws_ecs_cluster.main' bb-test-cluster
```

### "No valid credential sources"

Verify AWS credentials:

```bash
aws sts get-caller-identity
```

### Service Won't Start

```bash
# Check ECS service events
aws ecs describe-services \
  --cluster bb-test-cluster \
  --services bb-test-api \
  --query 'services[0].events[:5]'

# Check container logs
aws logs tail /aws/ecs/fargate/bb-test-api --since 30m
```

### ALB Health Checks Failing

```bash
# Check target health
aws elbv2 describe-target-health \
  --target-group-arn $(tofu output -raw target_group_arns | jq -r '.api')
```

---

## Quick Reference

| Action | Command |
|--------|---------|
| Initialize | `tofu init -var="parent_env=test"` |
| Select workspace | `tofu workspace select test` |
| Plan | `tofu plan` |
| Apply | `tofu apply` |
| Apply (no prompt) | `tofu apply -auto-approve` |
| Destroy | `tofu destroy` (confirm with team first) |
| Show outputs | `tofu output` |
| List resources | `tofu state list` |
| Import resource | `tofu import '<address>' <id>` |
| Format files | `tofu fmt -recursive` |
| Validate | `tofu validate` |
| Edit SOPS config | `bin/sopsw -e values/{env}.sopsw.yaml` |
