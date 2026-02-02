# IAM resources for CodeBuild

# Assume Role Policy
data "aws_iam_policy_document" "assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["codebuild.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "codebuild" {
  name                 = "${local.project_name}-role"
  path                 = var.iam_path
  permissions_boundary = var.permissions_boundary_arn
  assume_role_policy   = data.aws_iam_policy_document.assume_role.json

  tags = {
    Name = "${local.project_name}-role"
  }
}

# CloudWatch Logs Policy
data "aws_iam_policy_document" "logs" {
  statement {
    sid       = "AllowLogStreamControl"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.runner.arn}:*"]
  }
}

resource "aws_iam_role_policy" "logs" {
  name   = "logs"
  role   = aws_iam_role.codebuild.id
  policy = data.aws_iam_policy_document.logs.json
}

# GitHub Connection Policy
data "aws_iam_policy_document" "github" {
  statement {
    sid = "AllowGitHubConnection"
    actions = [
      "codestar-connections:GetConnectionToken",
      "codestar-connections:GetConnection",
      "codeconnections:GetConnectionToken",
      "codeconnections:GetConnection",
      "codeconnections:UseConnection"
    ]
    resources = [
      aws_codestarconnections_connection.github.arn,
      replace(aws_codestarconnections_connection.github.arn, "codestar-connections", "codeconnections")
    ]
  }
}

resource "aws_iam_role_policy" "github" {
  name   = "github"
  role   = aws_iam_role.codebuild.id
  policy = data.aws_iam_policy_document.github.json
}

# ECR Policy (for docker pull/push)
data "aws_iam_policy_document" "ecr" {
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
    resources = [var.ecr_repository_arn]
  }
}

resource "aws_iam_role_policy" "ecr" {
  name   = "ecr"
  role   = aws_iam_role.codebuild.id
  policy = data.aws_iam_policy_document.ecr.json
}

# KMS Policy (optional, for encrypted logs/ECR)
data "aws_iam_policy_document" "kms" {
  count = var.kms_key_arn != null ? 1 : 0

  statement {
    sid = "AllowKMSEncryptDecrypt"
    actions = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:DescribeKey"
    ]
    resources = [var.kms_key_arn]
  }
}

resource "aws_iam_role_policy" "kms" {
  count = var.kms_key_arn != null ? 1 : 0

  name   = "kms"
  role   = aws_iam_role.codebuild.id
  policy = data.aws_iam_policy_document.kms[0].json
}
