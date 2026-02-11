# Blue Button 2.0 Services

This directory follows the **CMS Cloud Terraservice Pattern** — numbered service layers with shared root configuration.

## Directory Structure

```
ops/services/
├── .opentofu-version           # OpenTofu 1.10.6
├── root.tofu.tf                # Shared backend/provider config (symlinked to all services)
│
├── 00-bootstrap/               # ECR, KMS, CodeBuild, GitHub OIDC
├── 01-config/                  # SOPS → SSM parameter provisioning
├── 10-cluster/                 # ECS Fargate Cluster
└── 20-microservices/           # ECS Services, ALB, IAM, Auto-scaling
```

## Symlinked Root Configuration

Each service directory contains a symlink to `root.tofu.tf`:
```
00-bootstrap/tofu.tf     -> ../root.tofu.tf
01-config/tofu.tf        -> ../root.tofu.tf
10-cluster/tofu.tf       -> ../root.tofu.tf
20-microservices/tofu.tf -> ../root.tofu.tf
```

The shared root provides:
- S3 backend: `bb-{bucket_env}-app-config` bucket, `ops/services/{service}/tofu.tfstate` key
- AWS provider `~> 6` with default tags
- Common locals: `app` (`bb`), `parent_env`, `bucket_env`, `default_tags`

Each service defines its own `local.env = terraform.workspace` and `local.service` (e.g., `"bootstrap"`, `"cluster"`, `"config"`, `"microservices"`).

## Service Numbering

| Prefix | Service | Purpose | Dependencies |
|--------|---------|---------|--------------|
| `00-` | bootstrap | ECR, KMS, CodeBuild, OIDC | None |
| `01-` | config | SOPS-encrypted config → SSM | 00-bootstrap (KMS) |
| `10-` | cluster | ECS Fargate Cluster | 00-bootstrap |
| `20-` | microservices | ECS Services, ALB, IAM | 01-config, 10-cluster |

## Initialize a Service

```bash
cd ops/services/<service>

# Initialize with parent environment (determines S3 bucket)
tofu init -var="parent_env=test"   # test account → bb-test-app-config
tofu init -var="parent_env=prod"   # prod account → bb-prod-app-config

# Select workspace
tofu workspace select test
```

## Deploy

```bash
# Deploy in dependency order
for dir in 00-bootstrap 01-config 10-cluster 20-microservices; do
  echo "=== Deploying $dir ==="
  (cd $dir && tofu apply -auto-approve)
done
```

## Service Details

### 00-bootstrap
Foundational resources shared across environments.

**Resources:**
- ECR repository (`bb-{env}-api`)
- KMS key alias (`alias/bb-{env}-app-key-alias`)
- CodeBuild project with GitHub connection
- GitHub Actions OIDC provider and IAM role

**Outputs:** `ecr_repository_url`, `codebuild_project_arn`, `github_actions_role_arn`

---

### 01-config
SOPS-managed configuration. Decrypts encrypted `.sopsw.yaml` files and provisions SSM parameters.

**Resources:**
- SSM parameters (SecureString for sensitive, String for non-sensitive)
- Local `sopsw` wrapper script

**Values files:** `values/{parent_env}.sopsw.yaml` (encrypted with KMS)

**Usage:**
```bash
# Edit encrypted config for test environment
bin/sopsw -e values/test.sopsw.yaml
```

**Outputs:** `sopsw` (edit command), `ssm_parameters`, `parameter_count`

---

### 10-cluster
ECS Fargate cluster shared by all application services.

**Resources:**
- ECS Cluster (`bb-{env}-cluster`) with Container Insights
- Capacity providers: FARGATE (base=1, weight=100), FARGATE_SPOT (available)
- CloudWatch log group for ECS Exec

**Outputs:** `cluster_id`, `cluster_arn`, `cluster_name`

---

### 20-microservices
ECS Fargate application services with ALB, auto-scaling, and IAM.

**Resources:**
- ECS services and task definitions (per `backend_services` variable)
- Application Load Balancer with HTTPS listener
- Target groups with HTTP health checks
- CloudWatch log groups
- Auto-scaling policies (CPU/memory-based)
- IAM execution and task roles (Secrets Manager, SSM, KMS, S3 access)
- Security groups (ALB and ECS)

**Configuration sources (priority order):**
1. `var.service_overrides` — Terraform variable overrides
2. SSM JSON parameter `/bb/{env}/{service}/config` — Per-service JSON config
3. Hardcoded defaults (cpu=512, memory=1024, port=8000, count=1)

**SSM JSON config format:**
```json
{
  "port": 8000,
  "cpu": 512,
  "memory": 1024,
  "count": 1,
  "scaling_min": 1,
  "scaling_max": 2,
  "health_check_path": "/health",
  "alb_enabled": true,
  "autoscale_enabled": false
}
```

**Secrets:** Auto-discovered from Secrets Manager under `/bb2/{env}/app/`. Infrastructure-only secrets are excluded (ssh_users, nessus, tfbackend, www certs).

**Cross-service discovery:** Uses AWS data sources (not remote state):
- `data.aws_ecs_cluster.main` — discovers cluster by name convention
- `data.aws_ecr_repository.api` — discovers ECR repo by name convention

**Outputs:** `service_names`, `alb_dns_names`, `target_group_arns`, `log_group_names`

## Backend Configuration

- **Bucket:** `bb-{bucket_env}-app-config` (sandbox uses prod bucket)
- **Key:** `ops/services/{service}/tofu.tfstate`
- **Encryption:** Enabled (KMS TODO)
- **Region:** `us-east-1`

## Environments

Managed via OpenTofu workspaces:

| Workspace | Account | State Bucket |
|-----------|---------|-------------|
| `test` | Test | `bb-test-app-config` |
| `sandbox` | Prod | `bb-prod-app-config` |
| `prod` | Prod | `bb-prod-app-config` |

## Validation

```bash
cd ops/services
for dir in 00-bootstrap 01-config 10-cluster 20-microservices; do
  echo "=== Validating $dir ==="
  (cd $dir && tofu validate)
done
```
