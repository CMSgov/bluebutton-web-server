# BB2 Services Runbook

## Prerequisites

- **OpenTofu** >= 1.8 (check with `tofu version`)
- **AWS credentials** configured for the target account
- **S3 state buckets** exist: `bb-test-app-config`, `bb-prod-app-config`

## Environments

| Workspace | Account | `TF_VAR_parent_env` |
|-----------|---------|---------------------|
| `test` | Non-Prod | `test` |
| `sandbox` | Prod | `prod` |
| `prod` | Prod | `prod` |

```bash
# Set once per shell session (sandbox shares prod's S3 bucket)
export TF_VAR_parent_env=test   # or prod
```

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

Full walkthrough using `test` as an example. Replace with `prod`/`sandbox` as needed.

```bash
# ============================================================
# BB2 Fargate — Full Deploy (test environment)
# ============================================================

# Prerequisites
export TF_VAR_parent_env=test
aws sts get-caller-identity   # verify credentials

# ============================================================
# Step 1: 00-bootstrap
# ============================================================
cd ops/services/00-bootstrap
tofu init
tofu workspace select test || tofu workspace new test

# Apply (webhook will fail — that's expected)
tofu plan
tofu apply

# Import the webhook into state
tofu import 'aws_codebuild_webhook.runner[0]' bb-test-web-server

# >>> MANUAL: AWS Console → Developer Tools → Connections
# >>> Approve "bb-github-connection" with GitHub
# >>> MANUAL: Delete stale webhooks at
# >>> https://github.com/CMSgov/bluebutton-web-server/settings/hooks

# Re-apply to create webhook (after connection is AVAILABLE)
tofu plan
tofu apply

# ============================================================
# Step 2: 01-config
# ============================================================
cd ../01-config
tofu init
tofu workspace select test || tofu workspace new test

# Create encrypted values from seed
cp values/test.sopsw.yaml.seed.minimal values/test.sopsw.yaml
bin/sopsw -e values/test.sopsw.yaml

tofu plan
tofu apply

# Verify
aws ssm get-parameters-by-path \
  --path "/bb/test/app" --recursive \
  --query 'Parameters[].{Name:Name,Type:Type}' --output table

# ============================================================
# Step 3: 10-cluster
# ============================================================
cd ../10-cluster
tofu init
tofu workspace select test || tofu workspace new test
tofu plan
tofu apply

# Verify
aws ecs describe-clusters --clusters bb-test-cluster \
  --query 'clusters[0].{name:clusterName,status:status}'

# ============================================================
# Step 4: 20-microservices
# ============================================================
cd ../20-microservices
tofu init
tofu workspace select test || tofu workspace new test
tofu plan
tofu apply

# Verify
tofu output alb_dns_names
aws ecs describe-services \
  --cluster bb-test-cluster \
  --services bb-test-api-service \
  --query 'services[0].{status:status,desired:desiredCount,running:runningCount}'
```

---

## Teardown (Reverse Order)

```bash
cd ops/services
for dir in 20-microservices 10-cluster 01-config 00-bootstrap; do
  echo "=== Destroying $dir ==="
  (cd $dir && tofu workspace select test && tofu destroy -auto-approve)
  echo ""
done
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

## CI/CD Workflows (GitHub Actions)

| Workflow | Trigger | Description |
|----------|---------|-------------|
| `tofu-plan` | PRs touching `ops/` | Runs `tofu plan` for all 3 envs |
| `tofu-apply` | Push to `main` + weekday schedule | Applies changes for all 3 envs |
| `tofu-fmt` | PRs touching `ops/` | Checks formatting |
| `tofu-bootstrap` | Manual only | First-time setup with approval gates |

All plan/apply workflows use `ops/scripts/tofu-plan` which runs services in dependency order. Apply mode stops on first failure; plan mode continues and reports all results.

**Required GitHub secrets:** `NON_PROD_ACCOUNT`, `PROD_ACCOUNT`, `SLACK_BOT_TOKEN`, `SLACK_CHANNEL_ID`

**Required GitHub environments** (with required reviewers): `bootstrap-approve`, `config-approve`, `cluster-approve`

---

## Switching Environments

The workspace determines which environment you operate on. `TF_VAR_parent_env` is needed for `tofu init` to select the S3 backend bucket.

```bash
# Switch to prod
export TF_VAR_parent_env=prod
cd ops/services/20-microservices
tofu workspace select prod
tofu plan
```

**If switching between accounts** (test <-> prod), re-initialize:

```bash
# Switching from test to prod account
export TF_VAR_parent_env=prod
tofu init -reconfigure
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
export TF_VAR_parent_env=test
tofu init -reconfigure
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
| Set parent env | `export TF_VAR_parent_env=test` |
| Initialize | `tofu init` |
| Re-initialize (switch account) | `tofu init -reconfigure` |
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
