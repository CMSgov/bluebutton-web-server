# CodeBuild Terraservice

Standalone infrastructure for CI/CD pipeline.

## Quick Start

```bash
# 1. Navigate to this directory
cd ops/terraform/services/codebuild

# 2. Initialize Terraform
tofu init

# 3. Select workspace (creates if doesn't exist)
tofu workspace select test || tofu workspace new test

# 4. Plan
tofu plan

# 5. Apply
tofu apply

# 6. IMPORTANT: Confirm GitHub connection in AWS Console
#    Developer Tools → Settings → Connections → Update pending connection
```

## Outputs

After apply, you'll get:
- `codebuild_project_name` - Use to trigger builds
- `ecr_repository_url` - Use in buildspec.yml

## Trigger a Build

```bash
aws codebuild start-build --project-name bb-test-web-server
```
