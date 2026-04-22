# ============================================================================
# bb-site-static CodeBuild Project - GitHub Actions Runner
# Single project in test account — deploys to Akamai NetStorage for all envs
# ============================================================================

# CloudWatch Logs
resource "aws_cloudwatch_log_group" "static_site" {
  count             = local.create_static_site ? 1 : 0
  name              = "/aws/codebuild/${local.static_site_project_name}"
  retention_in_days = 30
  # Uses AWS-managed S3 key (alias/aws/s3) to match the manually-created project
  kms_key_id        = "arn:aws:kms:us-east-1:${data.aws_caller_identity.current.account_id}:alias/aws/s3"
}

# CodeBuild Project - Acts as GitHub Actions Runner
resource "aws_codebuild_project" "static_site" {
  count = local.create_static_site ? 1 : 0

  name               = local.static_site_project_name
  description        = "Blue Button Static Site - GitHub Actions Runner"
  build_timeout      = 60
  project_visibility = "PRIVATE"
  service_role       = aws_iam_role.codebuild_static_site[0].arn
  # Uses AWS-managed S3 key (alias/aws/s3) to match the manually-created project
  encryption_key     = "arn:aws:kms:us-east-1:${data.aws_caller_identity.current.account_id}:alias/aws/s3"

  artifacts {
    type = "NO_ARTIFACTS"
  }

  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                       = "aws/codebuild/amazonlinux-aarch64-standard:3.0"
    image_pull_credentials_type = "CODEBUILD"
    privileged_mode             = false
    type                        = "ARM_CONTAINER"

    environment_variable {
      name  = "AWS_ACCOUNT_ID"
      value = data.aws_caller_identity.current.account_id
    }

    environment_variable {
      name  = "AWS_REGION"
      value = data.aws_region.current.id
    }
  }

  logs_config {
    cloudwatch_logs {
      status     = "ENABLED"
      group_name = aws_cloudwatch_log_group.static_site[0].name
    }
  }

  # No buildspec - GitHub Actions workflow defines the steps
  source {
    type            = "GITHUB"
    location        = var.static_site_github_repo_url
    git_clone_depth = 1

    auth {
      type     = "SECRETS_MANAGER"
      resource = data.aws_secretsmanager_secret.github_token[0].arn
    }

    git_submodules_config {
      fetch_submodules = false
    }
  }

  lifecycle {
    # Auth is managed via the console using a personal token stored in Secrets Manager
    # (secret name differs from /bb/${env}/gitpat). Ignoring to prevent Terraform
    # from overwriting the live credential on apply.
    ignore_changes = [source[0].auth]
  }
}

# Webhook for GitHub Actions Runner integration
resource "aws_codebuild_webhook" "static_site" {
  count        = local.create_static_site ? 1 : 0
  project_name = aws_codebuild_project.static_site[0].name
  build_type   = "BUILD"

  filter_group {
    filter {
      exclude_matched_pattern = false
      pattern                 = "WORKFLOW_JOB_QUEUED"
      type                    = "EVENT"
    }
  }
}
