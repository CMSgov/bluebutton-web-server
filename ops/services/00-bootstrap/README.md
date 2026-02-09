# Bootstrap Service

## Overview

Foundational infrastructure layer that provides shared resources required by all other services in the Blue Button environment.

## Resources Managed

### Container Infrastructure
- **ECR Repositories**: Docker image storage for application containers
- **KMS Keys**: Encryption keys for ECR and other services

### CI/CD Infrastructure  
- **CodeBuild Projects**: GitHub Actions runner integration
- **GitHub OIDC Provider**: Secure authentication for GitHub Actions workflows
- **IAM Roles**: 
  - CodeBuild service role with ECR/CloudWatch/GitHub permissions
  - GitHub Actions deployment role with OIDC trust

### Networking & Connectivity
- **GitHub CodeStar Connection**: Authenticated GitHub repository access
- **CloudWatch Log Groups**: CodeBuild execution logs

## Architecture

```
┌─────────────────────────────────────────┐
│         00-bootstrap                     │
├─────────────────────────────────────────┤
│                                          │
│  ECR Repos  ──┐                         │
│  KMS Keys   ──┼── Shared by all envs    │
│  CodeBuild  ──┤   (prod/sandbox)        │
│  OIDC       ──┘                         │
│                                          │
└─────────────────────────────────────────┘
         ▲              ▲
         │              │
    Test Account   Prod Account
    (separate)     (prod + sandbox)
```

## Environment Strategy

- **Test**: Separate AWS account, creates own resources
- **Prod**: Creates resources in prod account
- **Sandbox**: Reuses prod account resources (no creation)

## Initialization

### Prerequisites
1. S3 buckets must exist:
   - `bb-test-app-config` (Test account)
   - `bb-prod-app-config` (Prod account, shared by sandbox)

2. AWS credentials configured for target environment

### First-Time Setup

```bash
cd ops/services/00-bootstrap

# Initialize for prod environment
tofu init -var="parent_env=prod"

# Plan changes
tofu plan -var="parent_env=prod"

# Apply (creates ECR, CodeBuild, OIDC)
tofu apply -var="parent_env=prod"
```

### Manual Post-Deployment Steps

1. **Confirm GitHub Connection**
   - Navigate to AWS Console → Developer Tools → Settings → Connections
   - Find `bb-github-connection`
   - Click "Update pending connection" and authorize GitHub access

2. **Configure GitHub Actions Secrets**
   - Add the GitHub Actions role ARN to your repository secrets:
     ```bash
     AWS_ROLE_ARN: <github_actions_role_arn from outputs>
     ```

## Outputs

Key outputs for downstream services:

- `ecr_repository_url`: Container image registry URL
- `codebuild_project_arn`: CodeBuild project identifier
- `github_oidc_provider_arn`: OIDC provider for GitHub Actions
- `github_actions_role_arn`: IAM role for GitHub deployments

## Dependencies

- **Platform Module**: `../../modules/platform` (VPC, subnets, KMS discovery)
- **Root Config**: `../root.tofu.tf` (symlinked as `tofu.tf`)

## File Structure

```
00-bootstrap/
├── main.tf              # Platform module, ECR repositories, KMS keys
├── codebuild.tf         # CodeBuild project, GitHub connection
├── codebuild_iam.tf     # CodeBuild IAM role and policies
├── oidc.tf              # GitHub Actions OIDC provider and role
├── outputs.tf           # Resource outputs
├── variables.tf         # Input variables
└── tofu.tf             # Symlink to ../root.tofu.tf
```

## Notes

- Bootstrap must be applied before all other services
- Resources are shared between prod and sandbox (same AWS account)
- S3 state locking uses `use_lockfile = true` (no DynamoDB required)
- ECR lifecycle policy keeps last 30 tagged images
