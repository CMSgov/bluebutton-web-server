# Blue Button 2.0 Infrastructure

Infrastructure as Code for the Blue Button Web Server, managed via **OpenTofu** following the **CMS Cloud Terraservice Pattern**.

## Directory Structure

```
ops/
├── modules/                    # Shared local modules
│   ├── platform/               # VPC/subnet discovery, SSM, KMS, ACM, tags
│   └── sops/                   # SOPS decryption & SSM parameter provisioning
│
└── services/                   # Deployable service layers (numbered by dependency order)
    ├── .opentofu-version       # Version pinning (1.10.x)
    ├── root.tofu.tf            # Shared backend/provider config (symlinked to all services)
    │
    ├── 00-bootstrap/           # Foundational resources (ECR, CodeBuild, OIDC, KMS)
    ├── 01-config/              # SOPS-managed configuration (SSM parameter provisioning)
    ├── 10-cluster/             # ECS Fargate Cluster
    └── 20-microservices/       # Application services (ECS Services, ALB, IAM)
```

## Deployment Order

```
00-bootstrap    (ECR, KMS, CodeBuild, OIDC)
     ↓
01-config       (SOPS → SSM parameters)
     ↓
10-cluster      (ECS Fargate Cluster)
     ↓
20-microservices (ECS Services, ALB, Auto-scaling)
```

Always deploy top-to-bottom. Destroy bottom-to-top.

## Quick Start

```bash
# Set ENV and parent_env (sandbox shares prod's S3 bucket)
export ENV=test                        # test | sandbox | prod
export TF_VAR_parent_env=test          # test → test, sandbox/prod → prod

cd ops/services/<service>
tofu init
tofu workspace select $ENV || tofu workspace new $ENV
tofu plan
tofu apply
```

## Full Deploy

Replace `$ENV` with your target environment (`test`, `sandbox`, or `prod`).
Set `TF_VAR_parent_env` to `test` for test, or `prod` for sandbox/prod.

```bash
# ============================================================
# BB2 Fargate — Full Deploy
# ============================================================

# Prerequisites
export ENV=test                        # test | sandbox | prod
export TF_VAR_parent_env=test          # test → test, sandbox/prod → prod
aws sts get-caller-identity            # verify credentials

# ============================================================
# Step 1: 00-bootstrap
# ============================================================
cd ops/services/00-bootstrap
tofu init
tofu workspace select $ENV || tofu workspace new $ENV

# Apply (webhook will fail — that's expected)
tofu apply
tofu import 'aws_codebuild_webhook.runner[0]' bb-${ENV}-web-server

# >>> MANUAL: AWS Console → Developer Tools → Connections
# >>> Approve "bb-github-connection" with GitHub
# >>> MANUAL: Delete stale webhooks at
# >>> https://github.com/CMSgov/bluebutton-web-server/settings/hooks

# Re-apply to create webhook (after connection is AVAILABLE)
tofu apply

# ============================================================
# Step 2: 01-config
# ============================================================
cd ../01-config
tofu init
tofu workspace select $ENV || tofu workspace new $ENV

# Create encrypted values from seed
cp values/${ENV}.sopsw.yaml.seed.minimal values/${ENV}.sopsw.yaml
bin/sopsw -e values/${ENV}.sopsw.yaml

tofu plan
tofu apply

# Verify
aws ssm get-parameters-by-path \
  --path "/bb/${ENV}/app" --recursive \
  --query 'Parameters[].{Name:Name,Type:Type}' --output table

# ============================================================
# Step 3: 10-cluster
# ============================================================
cd ../10-cluster
export TF_VAR_parent_env=$TF_VAR_parent_env
tofu init
tofu workspace select $ENV || tofu workspace new $ENV
tofu plan
tofu apply

# Verify
aws ecs describe-clusters --clusters bb-${ENV}-cluster \
  --query 'clusters[0].{name:clusterName,status:status}'

# ============================================================
# Step 4: 20-microservices
# ============================================================
cd ../20-microservices
export TF_VAR_parent_env=$TF_VAR_parent_env
tofu init
tofu workspace select $ENV || tofu workspace new $ENV
tofu plan
tofu apply

# Verify
tofu output alb_dns_names
aws ecs describe-services \
  --cluster bb-${ENV}-cluster \
  --services bb-${ENV}-api-service \
  --query 'services[0].{status:status,desired:desiredCount,running:runningCount}'
```

## Teardown (Reverse Order)

```bash
cd ops/services
for dir in 20-microservices 10-cluster 01-config 00-bootstrap; do
  echo "=== Destroying $dir ==="
  (cd $dir && tofu workspace select $ENV && tofu destroy -auto-approve)
  echo ""
done
```

## CI/CD Workflows (GitHub Actions)

| Workflow | Trigger | Description |
|----------|---------|-------------|
| `tofu-plan` | PRs touching `ops/` | Runs `tofu plan` for all 3 envs |
| `tofu-apply` | Push to `main` + weekday schedule | Applies changes for all 3 envs |
| `tofu-fmt` | PRs touching `ops/` | Checks formatting |
| `tofu-bootstrap` | Manual only | First-time setup with approval gates |

All plan/apply workflows use `scripts/tofu-plan` which runs services in dependency order. Apply mode stops on first failure; plan mode continues and reports all results.

**Required GitHub secrets:** `NON_PROD_ACCOUNT`, `PROD_ACCOUNT`, `SLACK_BOT_TOKEN`, `SLACK_CHANNEL_ID`

**Required GitHub environments** (with required reviewers): `bootstrap-approve`, `config-approve`, `cluster-approve`

## Key Concepts

### Root Configuration (`root.tofu.tf`)
Every service directory contains `tofu.tf` — a **symlink** to `root.tofu.tf`. This provides:
- **Dynamic S3 backend**: `bb-{bucket_env}-app-config` bucket, `ops/services/{service}/tofu.tfstate` key
- **AWS provider** (`~> 6`) with default tags
- **Standard locals**: `app`, `parent_env`, `bucket_env`, `default_tags`

### Platform Module (`modules/platform`)
Shared data lookups used by all services:
- VPC and subnet discovery (by tag)
- KMS key alias resolution
- ACM certificate lookup
- SSM parameter loading (`/bb/` hierarchy)
- IAM permissions boundary
- Standard tags (application, business, environment, service, opentofu)

### SOPS Module (`modules/sops`)
Decrypts encrypted `.sopsw.yaml` values files and provisions SSM parameters:
- Uses `sopsw` wrapper script for `${ACCOUNT_ID}` substitution
- Sensitive values → SSM `SecureString` (KMS-encrypted)
- Non-sensitive values (path contains `nonsensitive`) → SSM `String`

### Environments
Managed via OpenTofu workspaces:
- **test** — Test AWS account (`bb-test-app-config` bucket)
- **sandbox** — Prod AWS account (`bb-prod-app-config` bucket, shared with prod)
- **prod** — Prod AWS account (`bb-prod-app-config` bucket)

### Cross-Service References
Services discover each other via **AWS data sources** (not `terraform_remote_state`):
```hcl
# 20-microservices discovers cluster by name convention
data "aws_ecs_cluster" "main" {
  cluster_name = "bb-${local.workspace}-cluster"
}

# 20-microservices discovers ECR repo by name convention
data "aws_ecr_repository" "api" {
  name = "bb-${local.bucket_env}-api"
}
```

## Documentation

- [Services RUNBOOK](services/RUNBOOK.md) — Full runbook with day-to-day operations and troubleshooting
- [Services README](services/README.md) — Service details and architecture
- [Naming Conventions](services/NAMING.md) — Resource naming patterns
