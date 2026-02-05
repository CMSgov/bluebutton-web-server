# Blue Button CodeBuild Module
# Includes: CodeBuild runner, ECR, GitHub Actions OIDC

locals {
  project_name = "bb-${var.env}-web-server"
}

# ============================================================================
# ECR Repository for storing built images
# ============================================================================
resource "aws_ecr_repository" "api" {
  name                 = "bb-${var.env}-api"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "bb-${var.env}-api"
  }
}

resource "aws_ecr_lifecycle_policy" "api" {
  repository = aws_ecr_repository.api.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 30 images"
      selection = {
        tagStatus     = "tagged"
        tagPrefixList = ["v"]
        countType     = "imageCountMoreThan"
        countNumber   = 30
      }
      action = { type = "expire" }
    }]
  })
}

# ============================================================================
# GitHub Connection (CodeStar)
# NOTE: After first apply, manually confirm in AWS Console:
# Developer Tools → Settings → Connections → Update pending connection
# ============================================================================
resource "aws_codestarconnections_connection" "github" {
  name          = "bb-github-connection"
  provider_type = "GitHub"
}

resource "aws_codebuild_source_credential" "github" {
  auth_type   = "CODECONNECTIONS"
  server_type = "GITHUB"
  token       = aws_codestarconnections_connection.github.arn
}

# ============================================================================
# CloudWatch Logs
# ============================================================================
resource "aws_cloudwatch_log_group" "runner" {
  name              = "/aws/codebuild/${local.project_name}"
  retention_in_days = 30
  kms_key_id        = var.kms_key_arn
}

# ============================================================================
# CodeBuild Project - Acts as GitHub Actions Runner
# ============================================================================
resource "aws_codebuild_project" "main" {
  depends_on = [aws_codebuild_source_credential.github]

  name               = local.project_name
  description        = "Blue Button Web Server - GitHub Actions Runner"
  build_timeout      = 60
  project_visibility = "PRIVATE"
  service_role       = aws_iam_role.codebuild.arn

  artifacts {
    type = "NO_ARTIFACTS"
  }

  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                       = "aws/codebuild/amazonlinux2-aarch64-standard:3.0"
    image_pull_credentials_type = "CODEBUILD"
    privileged_mode             = true # Required for Docker builds
    type                        = "ARM_CONTAINER"

    environment_variable {
      name  = "ECR_URI"
      value = aws_ecr_repository.api.repository_url
    }

    environment_variable {
      name  = "AWS_ACCOUNT_ID"
      value = data.aws_caller_identity.current.account_id
    }

    environment_variable {
      name  = "AWS_REGION"
      value = data.aws_region.current.name
    }
  }

  logs_config {
    cloudwatch_logs {
      status     = "ENABLED"
      group_name = aws_cloudwatch_log_group.runner.name
    }
  }

  # No buildspec - GitHub Actions workflow defines the steps
  source {
    type            = "GITHUB"
    location        = var.github_repo_url
    git_clone_depth = 1

    git_submodules_config {
      fetch_submodules = false
    }
  }
}

# Webhook for GitHub Actions Runner integration
resource "aws_codebuild_webhook" "runner" {
  project_name = aws_codebuild_project.main.name
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
