# IAM resources for bb-site-static CodeBuild
# Only created in test account

resource "aws_iam_role" "codebuild_static_site" {
  count                = local.create_static_site ? 1 : 0
  name                 = "codebuild-${local.static_site_project_name}-service-role"
  path                 = "/service-role/"
  permissions_boundary = local.permissions_boundary
  assume_role_policy   = data.aws_iam_policy_document.assume_role.json

  tags = {
    Name = "codebuild-${local.static_site_project_name}-service-role"
  }
}

# ============================================================================
# Inline Policy: CloudWatch Logs (imported from manual setup)
# ============================================================================
data "aws_iam_policy_document" "static_site_logs" {
  count = local.create_static_site ? 1 : 0

  statement {
    sid       = "AllowLogStreamControl"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.static_site[0].arn}:*"]
  }
}

resource "aws_iam_role_policy" "static_site_logs" {
  count  = local.create_static_site ? 1 : 0
  name   = "cloudwatch-logs-access"
  role   = aws_iam_role.codebuild_static_site[0].id
  policy = data.aws_iam_policy_document.static_site_logs[0].json
}

# ============================================================================
# Managed Policies (imported from console auto-created policies)
# These can be replaced with inline policies later to match web-server pattern
# ============================================================================
resource "aws_iam_policy" "static_site_codebuild_base" {
  count       = local.create_static_site ? 1 : 0
  name        = "CodeBuildBasePolicy-${local.static_site_project_name}-us-east-1"
  path        = "/service-role/"
  description = "Policy used in trust relationship with CodeBuild"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "arn:aws:logs:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:log-group:/aws/codebuild/${local.static_site_project_name}",
          "arn:aws:logs:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:log-group:/aws/codebuild/${local.static_site_project_name}:*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:GetObjectVersion",
          "s3:GetBucketAcl",
          "s3:GetBucketLocation"
        ]
        Resource = "arn:aws:s3:::codepipeline-${data.aws_region.current.id}-*"
      },
      {
        Effect = "Allow"
        Action = [
          "codebuild:CreateReportGroup",
          "codebuild:CreateReport",
          "codebuild:UpdateReport",
          "codebuild:BatchPutTestCases",
          "codebuild:BatchPutCodeCoverages"
        ]
        Resource = "arn:aws:codebuild:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:report-group/${local.static_site_project_name}-*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "static_site_codebuild_base" {
  count      = local.create_static_site ? 1 : 0
  role       = aws_iam_role.codebuild_static_site[0].name
  policy_arn = aws_iam_policy.static_site_codebuild_base[0].arn
}

resource "aws_iam_policy" "static_site_secrets_manager" {
  count       = local.create_static_site ? 1 : 0
  name        = "CodeBuildSecretsManagerSourceCredentialsPolicy-${local.static_site_project_name}-us-east-1"
  path        = "/service-role/"
  description = "Policy used in trust relationship with CodeBuild"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "secretsmanager:GetSecretValue"
        Resource = data.aws_secretsmanager_secret.github_token[0].arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "static_site_secrets_manager" {
  count      = local.create_static_site ? 1 : 0
  role       = aws_iam_role.codebuild_static_site[0].name
  policy_arn = aws_iam_policy.static_site_secrets_manager[0].arn
}


# ============================================================================
# GitHub Connection Policy (new - needed for CodeConnections)
# ============================================================================
data "aws_iam_policy_document" "static_site_github" {
  count = local.create_static_site ? 1 : 0

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

resource "aws_iam_role_policy" "static_site_github" {
  count  = local.create_static_site ? 1 : 0
  name   = "github"
  role   = aws_iam_role.codebuild_static_site[0].id
  policy = data.aws_iam_policy_document.static_site_github[0].json
}

# ============================================================================
# KMS Policy (new - for encrypted CloudWatch logs)
# ============================================================================
data "aws_iam_policy_document" "static_site_kms" {
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

resource "aws_iam_role_policy" "static_site_kms" {
  count = local.kms_key_arn != null && local.create_static_site ? 1 : 0

  name   = "kms"
  role   = aws_iam_role.codebuild_static_site[0].id
  policy = data.aws_iam_policy_document.static_site_kms[0].json
}
