# ============================================================================
# GitHub Connection (CodeStar)
# NOTE: After first apply, manually confirm in AWS Console:
# Developer Tools → Settings → Connections → Update pending connection
# ============================================================================
resource "aws_codestarconnections_connection" "github" {
  count         = local.create_resources ? 1 : 0
  name          = "bb-github-connection"
  provider_type = "GitHub"
}

# Disabled: PAT via Secrets Manager is the active auth. The source credential
# was imported manually (aws codebuild import-source-credentials) and is not
# managed by tofu. Re-enable when switching to CodeConnections.
# resource "aws_codebuild_source_credential" "github" {
#   count       = local.create_resources ? 1 : 0
#   auth_type   = "CODECONNECTIONS"
#   server_type = "GITHUB"
#   token       = aws_codestarconnections_connection.github[0].arn
# }

# ============================================================================
# CloudWatch Logs
# ============================================================================
resource "aws_cloudwatch_log_group" "runner" {
  count             = local.create_resources ? 1 : 0
  name              = "/aws/codebuild/${local.project_name}"
  retention_in_days = 30
  kms_key_id        = local.kms_key_arn
}

# ============================================================================
# CodeBuild Project - Acts as GitHub Actions Runner
# ============================================================================
resource "aws_codebuild_project" "main" {
  count = local.create_resources ? 1 : 0

  name               = local.project_name
  description        = "Blue Button Web Server - GitHub Actions Runner"
  build_timeout      = 60
  project_visibility = "PRIVATE"
  service_role       = aws_iam_role.codebuild[0].arn

  artifacts {
    type = "NO_ARTIFACTS"
  }

  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                       = "aws/codebuild/amazonlinux-aarch64-standard:3.0"
    image_pull_credentials_type = "CODEBUILD"
    privileged_mode             = true # Required for Docker builds
    type                        = "ARM_CONTAINER"

    environment_variable {
      name  = "ECR_URI"
      value = aws_ecr_repository.api[0].repository_url
    }

    environment_variable {
      name  = "AWS_ACCOUNT_ID"
      value = data.aws_caller_identity.current.account_id
    }

    environment_variable {
      name  = "AWS_REGION"
      value = data.aws_region.current.region
    }
  }

  logs_config {
    cloudwatch_logs {
      status     = "ENABLED"
      group_name = aws_cloudwatch_log_group.runner[0].name
    }
  }

  # No buildspec - GitHub Actions workflow defines the steps
  source {
    type            = "GITHUB"
    location        = var.github_repo_url
    git_clone_depth = 1

    auth {
      type     = "SECRETS_MANAGER"
      resource = data.aws_secretsmanager_secret.github_token[0].arn
    }

    git_submodules_config {
      fetch_submodules = false
    }
  }

  # same network as the api task so integration tests can reach BFD test
  dynamic "vpc_config" {
    for_each = local.runner_vpc_ready ? [1] : []
    content {
      vpc_id             = local.vpc_id
      subnets            = local.private_subnet_ids
      security_group_ids = [one(data.aws_security_groups.runner_api[0].ids), data.aws_security_group.runner_shared[0].id]
    }
  }

  lifecycle {
    ignore_changes = [source[0].auth]
  }
}

# Webhook for GitHub Actions Runner integration
resource "aws_codebuild_webhook" "runner" {
  count        = local.create_resources ? 1 : 0
  project_name = aws_codebuild_project.main[0].name
  build_type   = "BUILD"

  filter_group {
    filter {
      exclude_matched_pattern = false
      pattern                 = "WORKFLOW_JOB_QUEUED"
      type                    = "EVENT"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# api sg is owned by 20-microservices. plural lookup so a fresh env skips the vpc instead of erroring
data "aws_security_groups" "runner_api" {
  count = local.runner_in_vpc ? 1 : 0

  filter {
    name   = "group-name"
    values = ["bb-${local.env}-ecs-api-sg"]
  }

  filter {
    name   = "vpc-id"
    values = [local.vpc_id]
  }
}

# CMS Cloud managed, don't touch
data "aws_security_group" "runner_shared" {
  count  = local.runner_vpc_ready ? 1 : 0
  name   = "cmscloud-shared-services"
  vpc_id = local.vpc_id
}

data "aws_secretsmanager_secret" "github_token" {
  count = local.create_resources ? 1 : 0
  name  = "/bb/${local.env}/gitpat"
}

# don't let the runner quietly fall out of the vpc, integration tests would just start failing on dns
check "runner_in_vpc" {
  assert {
    condition     = local.runner_vpc_ready == local.runner_in_vpc
    error_message = "bb-${local.env}-ecs-api-sg not found, runner is NOT in the vpc. apply 20-microservices then re-run bootstrap"
  }
}
