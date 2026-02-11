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
  count                = local.create_resources ? 1 : 0
  name                 = "${local.project_name}-role"
  path                 = var.iam_path
  permissions_boundary = local.permissions_boundary
  assume_role_policy   = data.aws_iam_policy_document.assume_role.json

  tags = {
    Name = "${local.project_name}-role"
  }
}

# CloudWatch Logs Policy
data "aws_iam_policy_document" "logs" {
  count = local.create_resources ? 1 : 0

  statement {
    sid       = "AllowLogStreamControl"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.runner[0].arn}:*"]
  }
}

resource "aws_iam_role_policy" "logs" {
  count  = local.create_resources ? 1 : 0
  name   = "logs"
  role   = aws_iam_role.codebuild[0].id
  policy = data.aws_iam_policy_document.logs[0].json
}

# GitHub Connection Policy
data "aws_iam_policy_document" "github" {
  count = local.create_resources ? 1 : 0

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
      aws_codestarconnections_connection.github[0].arn,
      replace(aws_codestarconnections_connection.github[0].arn, "codestar-connections", "codeconnections")
    ]
  }
}

resource "aws_iam_role_policy" "github" {
  count  = local.create_resources ? 1 : 0
  name   = "github"
  role   = aws_iam_role.codebuild[0].id
  policy = data.aws_iam_policy_document.github[0].json
}

# ECR Policy (for docker pull/push)
data "aws_iam_policy_document" "ecr" {
  count = local.create_resources ? 1 : 0

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
    resources = [aws_ecr_repository.api[0].arn]
  }
}

resource "aws_iam_role_policy" "ecr" {
  count  = local.create_resources ? 1 : 0
  name   = "ecr"
  role   = aws_iam_role.codebuild[0].id
  policy = data.aws_iam_policy_document.ecr[0].json
}

# KMS Policy (optional, for encrypted logs/ECR)
data "aws_iam_policy_document" "kms" {
  count = local.kms_key_arn != null ? 1 : 0

  statement {
    sid = "AllowKMSEncryptDecrypt"
    actions = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:DescribeKey"
    ]
    resources = [local.kms_key_arn]
  }
}

resource "aws_iam_role_policy" "kms" {
  count = local.kms_key_arn != null && local.create_resources ? 1 : 0

  name   = "kms"
  role   = aws_iam_role.codebuild[0].id
  policy = data.aws_iam_policy_document.kms[0].json
}
