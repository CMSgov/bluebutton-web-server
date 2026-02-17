# GitHub Actions OIDC Authentication
# Allows GitHub Actions to assume an AWS IAM role via OIDC

# OIDC Provider for GitHub Actions
# Created once per AWS account (not per environment)
# Sandbox reuses the provider created by prod (same account)
resource "aws_iam_openid_connect_provider" "github_actions" {
  count = local.create_resources ? 1 : 0 # Only create in test and prod, not sandbox

  client_id_list = ["sts.amazonaws.com"]
  url            = "https://token.actions.githubusercontent.com"

  # GitHub's OIDC thumbprint (standard, rarely changes)
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

# Discover OIDC provider (works for all workspaces including sandbox)
data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  depends_on = [aws_iam_openid_connect_provider.github_actions]
}

# Trust policy: Allow GitHub Actions from this repo to assume the role
data "aws_iam_policy_document" "github_actions_assume_role" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [data.aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_org}/${var.github_repo}:*"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

# IAM Role for GitHub Actions (created per environment)
resource "aws_iam_role" "github_actions" {
  name                 = "bb-${local.env}-github-actions"
  path                 = var.iam_path
  permissions_boundary = local.permissions_boundary
  description          = "OIDC Assumable GitHub Actions Role for Blue Button"

  assume_role_policy    = data.aws_iam_policy_document.github_actions_assume_role.json
  force_detach_policies = true

  tags = {
    Name = "bb-${local.env}-github-actions"
  }
}

# ============================================================================
# Discover shared resources (ECR & CodeBuild) by name
# For prod/test: finds the resource we just created
# For sandbox: finds prod's resources (same account, bucket_env maps sandbox→prod)
# ============================================================================

data "aws_ecr_repository" "shared" {
  name = "bb-${local.bucket_env}-api"

  depends_on = [aws_ecr_repository.api]
}

# ============================================================================
# ECR permissions for GitHub Actions (push/pull images)
# All environments get this policy — sandbox references prod's ECR
# ============================================================================

data "aws_iam_policy_document" "github_actions_ecr" {
  statement {
    sid       = "AllowECRAuthorization"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    sid = "AllowECRImageOperations"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:PutImage",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload"
    ]
    resources = [data.aws_ecr_repository.shared.arn]
  }
}

resource "aws_iam_role_policy" "github_actions_ecr" {
  name   = "ecr"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.github_actions_ecr.json
}

# ============================================================================
# CodeBuild trigger permissions (to trigger builds from GHA)
# Only for environments that have a CodeBuild project (test, prod — not sandbox)
# ============================================================================

data "aws_iam_policy_document" "github_actions_codebuild" {
  count = local.create_resources ? 1 : 0

  statement {
    sid = "AllowCodeBuildTrigger"
    actions = [
      "codebuild:StartBuild",
      "codebuild:BatchGetBuilds"
    ]
    resources = [aws_codebuild_project.main[0].arn]
  }
}

resource "aws_iam_role_policy" "github_actions_codebuild" {
  count  = local.create_resources ? 1 : 0
  name   = "codebuild"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.github_actions_codebuild[0].json
}
