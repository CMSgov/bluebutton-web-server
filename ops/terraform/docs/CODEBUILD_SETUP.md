# CodeBuild + GitHub Actions Setup Guide

This guide explains how to set up AWS CodeBuild as a GitHub Actions self-hosted runner for the Blue Button Web Server.

## Architecture Overview

```
GitHub Actions Workflow
        │
        │ WORKFLOW_JOB_QUEUED event
        ▼
AWS CodeBuild Runner (bb-{env}-web-server)
        │
        │ Executes workflow steps
        ▼
Docker Build → ECR Push (bb-{env}-api)
```

The CodeBuild infrastructure is managed by the `bb-codebuild` module, which is deployed as part of the main services stack.

---

## Prerequisites

1. **AWS Account** with permissions to create CodeBuild, IAM, and ECR resources
2. **GitHub repository** admin access (required for webhook creation)
3. **Terraform/OpenTofu** installed locally

---

## Step-by-Step Setup

### Step 1: Deploy Infrastructure

CodeBuild is deployed as part of the main services stack:

```bash
cd ops/terraform/services

# Initialize
tofu init

# Select workspace
tofu workspace select test  # or sandbox, prod

# Apply (includes ECS, CodeBuild, and all other resources)
tofu apply
```

The `bb-codebuild` module creates:
- ECR repository (`bb-{env}-api`)
- CodeBuild project (`bb-{env}-web-server`)
- GitHub OIDC provider
- IAM roles for CodeBuild and GitHub Actions

### Step 2: Confirm GitHub CodeStar Connection

1. Go to **AWS Console** → **Developer Tools** → **Settings** → **Connections**
2. Find `bb-github-connection`
3. Click **Update pending connection**
4. Authorize with GitHub

> ⚠️ **Important**: The GitHub account used must have **admin access** to the repository.

### Step 3: Resolve Webhook Permission Error

If you see this error:
```
OAuthProviderException: Failed to create webhook. GitHub API limit reached 
or permission issue encountered when creating the webhook.
```

**Solution**: Add the GitHub account (used to confirm the connection) as a **collaborator with admin access** to the repository:

1. Go to **GitHub repo** → **Settings** → **Collaborators and teams**
2. Click **Add people**
3. Add the personal account that confirmed the CodeStar connection
4. Grant **Admin** role
5. Re-run `tofu apply`

### Step 4: Add GitHub Secrets

1. Go to **GitHub repo** → **Settings** → **Secrets and variables** → **Actions**
2. Add these repository secrets:

| Secret Name | Value |
|-------------|-------|
| `AWS_ROLE_ARN_TEST` | `arn:aws:iam::ACCOUNT_ID:role/bb-test-github-actions` |
| `AWS_ROLE_ARN_SANDBOX` | `arn:aws:iam::ACCOUNT_ID:role/bb-sandbox-github-actions` |
| `AWS_ROLE_ARN_PROD` | `arn:aws:iam::ACCOUNT_ID:role/bb-prod-github-actions` |

Get the role ARN from Terraform output:
```bash
cd ops/terraform/services
tofu output github_actions_role_arn
```

### Step 5: Push and Trigger Build

```bash
git add .
git commit -m "Add CI/CD pipeline"
git push
```

The workflow will automatically run on push to `main` or `develop`.

---

## Verify Setup

### Check Workflow Run
- Go to **GitHub repo** → **Actions** tab
- You should see "Build and Deploy" workflow

### Check CodeBuild Logs
```bash
aws logs tail /aws/codebuild/bb-test-web-server --follow
```

### View Terraform Outputs
```bash
cd ops/terraform/services
tofu output codebuild_project_name
tofu output codebuild_ecr_repository_url
tofu output github_actions_role_arn
```

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| `OAuthProviderException` | Add personal account as repo admin (Step 3) |
| `Connection pending` | Confirm connection in AWS Console (Step 2) |
| `Could not assume role` | Verify GitHub secret matches IAM role ARN |
| `Project not found` | Ensure `tofu apply` completed successfully |

---

## Module Reference

The CodeBuild resources are defined in [`modules/bb-codebuild/`](../modules/bb-codebuild/):

| File | Purpose |
|------|---------|
| `main.tf` | CodeBuild project, ECR repository, CloudWatch logs |
| `iam.tf` | CodeBuild service role and policies |
| `oidc.tf` | GitHub Actions OIDC provider and role |
| `variables.tf` | Input variables (env, IAM path, permissions boundary) |
| `outputs.tf` | Project name, ECR URL, GitHub Actions role ARN |

---

## How It Works

1. **Push to GitHub** → Triggers workflow
2. **GitHub sends `WORKFLOW_JOB_QUEUED`** → AWS webhook receives it
3. **CodeBuild starts** → Runs workflow steps in AWS
4. **Steps execute** → Docker build, ECR push, etc.
5. **Results reported** → Back to GitHub Actions UI

This eliminates the need for `buildspec.yml` - the workflow YAML defines all build steps.

