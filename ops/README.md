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

## Quick Start

```bash
cd ops/services/<service>

# Initialize (parent_env determines which S3 bucket for state)
tofu init -var="parent_env=test"    # test account
tofu init -var="parent_env=prod"    # prod/sandbox account

# Select workspace
tofu workspace select test

# Plan and apply
tofu plan
tofu apply
```

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

- [Services README](services/README.md) — Service details and architecture
- [Naming Conventions](services/NAMING.md) — Resource naming patterns
