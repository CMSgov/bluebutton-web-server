# Blue Button 2.0 - CMS Cloud-Style Infrastructure

This directory follows the **CMS Cloud multi-service architecture pattern** for terraform-managed infrastructure.

## 📁 Directory Structure

```
## 📁 Directory Structure

```
ops/services/
├── .opentofu-version       # OpenTofu 1.10.6
├── root.tofu.tf            # Shared backend/provider config (symlinked to all services)
├── 00-bootstrap/           # State management infrastructure
├── 10-cluster/             # ECS Cluster infrastructure (replacing 10-core)
├── 20-microservices/       # Application services (ECS Services)
└── 30-codebuild/           # CI/CD pipeline (GitHub Actions + CodeBuild)
```

## 🔧 How It Works

### Symlinked Root Configuration

Each service directory contains a **symlink** to `root.tofu.tf`:
```bash
00-bootstrap/tofu.tf -> ../root.tofu.tf
10-cluster/tofu.tf   -> ../root.tofu.tf
20-microservices/tofu.tf       -> ../root.tofu.tf
30-codebuild/tofu.tf -> ../root.tofu.tf
```

**Benefits:**
- ✅ **DRY**: Single source of truth for backend/provider config
- ✅ **Consistency**: All services use identical setup
- ✅ **Easy updates**: Change once, applies everywhere

### Service Numbering

Services are numbered by deployment order and dependencies:

| Prefix | Purpose | Dependencies |
|--------|---------|--------------|
| `00-` | Bootstrap (foundational) | None |
| `10-` | Cluster (infrastructure) | 00-bootstrap |
| `20-` | Application services | 10-cluster |
| `30-` | CI/CD & tooling | 10-cluster |

### Initialize a Service

We use the **OpenTofu 1.8+ dynamic backend** feature following the BFD pattern, allowing locals and variables in the backend block.

## Backend Configuration

- **Bucket**: `bb-{env}-app-config` (dynamically resolved from workspace)
- **Key**: `ops/services/{service}/tofu.tfstate`
- **Encryption**: KMS with `alias/bb-{env}-cmk`
- **State Locking**: OpenTofu lockfile (`use_lockfile = true`)

To initialize a service (e.g., `10-cluster`):

```bash
cd ops/services/10-cluster

# Initialize with parent environment
tofu init -var="parent_env=test"  # For test account
tofu init -var="parent_env=prod"  # For prod/sandbox account

# Select or create the workspace
tofu workspace select test || tofu workspace new test
```

**Why `-var="parent_env=X"`?** During initialization, OpenTofu needs to know which bucket to connect to before the workspace is selected. After init, the workspace name automatically determines the environment.

### 🌍 Two-account setup (prod/sandbox vs test)
- **Prod and Sandbox** share the `bb-prod-app-config` bucket (Prod AWS Account)
- **Test** uses the `bb-test-app-config` bucket (Test AWS Account)

### Deploy a Service

```bash
cd ops/services/20-microservices

# Plan changes
tofu plan

# Apply changes
tofu apply
```

### Deploy All Services

```bash
cd ops/services

# Deploy in order (respecting dependencies)
for dir in 00-bootstrap 10-cluster 20-microservices 30-codebuild; do
  echo "=== Deploying $dir ==="
  (cd $dir && tofu apply -auto-approve)
done
```

## 📦 Service Details

### 00-bootstrap
**Purpose:** State management infrastructure

**Resources:**
- State bucket (already exists: `bb2-terraform-state`)
- DynamoDB state locking (optional)

**Dependencies:** None

---

### 10-cluster
**Purpose:** ECS Cluster Infrastructure

**Resources:**
- ECS Fargate Cluster (`bb-{env}-cluster`)
- Capacity Providers (FARGATE, FARGATE_SPOT)
- Container Insights
- CloudWatch Log Groups (with KMS)

**Dependencies:** 00-bootstrap

**Outputs:**
- `cluster_id`
- `cluster_arn`
- `cluster_name`
- `capacity_providers`

---

### 20-microservices
**Purpose:** ECS Application Services

**Resources:**
- ECS Services (API, Worker, etc.)
- Task Definitions
- Application Load Balancer (ALB)
- Auto-scaling configuration
- Security groups

**Dependencies:** 10-cluster (via remote state)

**Inputs:**
- `image_tag` - Docker image tag (optional)
- `force_deployment` - Force new deployment (default: false)

**Outputs:**
- `ecs_service_names`
- `alb_dns_names`

---

### 30-codebuild
**Purpose:** CI/CD pipeline

**Resources:**
- CodeBuild project
- ECR repository
- GitHub Actions OIDC
- SNS topic for alarms

**Dependencies:** 10-cluster

**Outputs:**
- `codebuild_project_name`
- `github_actions_role_arn`
- `codebuild_ecr_repository_url`
- `sns_topic_arn`

## 🔐 State Management

### State Files

Each service has its own state file:

```
s3://bb-prod-tfstate/ (Shared Account: Prod & Sandbox)
├── ops/services/bootstrap/tofu.tfstate
├── ops/services/cluster/tofu.tfstate
├── ops/services/microservices/tofu.tfstate
└── ops/services/codebuild/tofu.tfstate

s3://bb-test-tfstate/ (Test Account)
└── ...
```

**Note:** `sandbox` and `prod` share the `bb-prod-tfstate` bucket because they reside in the same AWS account. This is configured in `root.tofu.tf`.

### State Locking

State locking is **enabled** via `use_lockfile = true` in `root.tofu.tf`.

## 🌍 Environments

Environments are managed via **OpenTofu workspaces**:

```bash
# List workspaces
tofu workspace list

# Create new workspace
tofu workspace new dev

# Switch workspace
tofu workspace select test
```

**Supported environments:**
- `dev`
- `test`
- `impl`
- `prod`

## 📋 Migration from ops/terraform

### Differences

| Aspect | Old (ops/terraform) | New (ops/services) |
|--------|-------------------|---------------|
| Structure | Single `services/` | Numbered dirs |
| Config | `backend.tf` per service | Symlinked `root.tofu.tf` |
| State | Monolithic | Per-service |
| Deployment | All-or-nothing | Independent |

### Migration Steps

1. **Test in dev first:**
   ```bash
   cd ops/services/20-microservices
   tofu workspace select dev
   tofu plan  # Should show no changes if configs match
   ```

2. **Import existing state (if needed):**
   ```bash
   tofu state pull > old-state.json
   # Review and import resources as needed
   ```

3. **Deploy incrementally:**
   - 00-bootstrap (likely no-op)
   - 10-core (verify discovery)
   - 20-microservices (main service)
   - 30-codebuild (CI/CD)

## 🎯 Best Practices

### When to Deploy Which Service

**00-bootstrap:** Only once during initial setup

**10-core:** (Deprecated/Removed)
**10-cluster:** When:
- Changing cluster settings (Container Insights, Capacity Providers)
- Updating KMS encryption keys

**20-microservices:** When:
- Deploying new container images
- Changing ECS configuration
- Updating ALB settings
- Scaling changes

**30-codebuild:** When:
- Updating CI/CD pipeline
- Changing GitHub Actions runners
- ECR policy changes

### Independent Deployments

One of the key benefits of this structure is **independent deployments**:

```bash
# Only deploy ECS changes (fast!)
cd ops/services/20-microservices && tofu apply

# Only deploy CodeBuild changes
cd ops/services/30-codebuild && tofu apply
```

**Benefits:**
- ✅ Faster deployments
- ✅ Smaller blast radius
- ✅ Parallel team work
- ✅ Clearer change visibility

## ⚠️ Important Notes

1. **State isolation:** Each service has separate state = lower blast radius

2. **Dependencies:** Deploy in order on first run:
   ```
   00-bootstrap → 10-cluster → 20-microservices
                              ↘ 30-codebuild
   ```

3. **Backend changes:** Editing `root.tofu.tf` affects **all services**

4. **Cross-service references:**
   - Use `terraform_remote_state` data source
   - Or re-run platform module in each service (current approach)

## 🔍 Validation

Validate all services:

```bash
cd ops/services
for dir in 00-bootstrap 10-cluster 20-microservices 30-codebuild; do
  echo "=== Validating $dir ==="
  (cd $dir && tofu validate)
done
```

## 📚 Additional Resources

- [CMS Cloud Repository](https://github.com/CMSgov/cms-cloud) - Reference implementation
- [Terraservice Pattern](https://github.com/CMSgov/cdap) - CMS platform modules
- [Final Structure Comparison](../STRUCTURE_COMPARISON.md)

---

**Created:** February 2026  
**Pattern:** CMS Cloud Multi-Service Architecture  
**OpenTofu Version:** 1.10.6
