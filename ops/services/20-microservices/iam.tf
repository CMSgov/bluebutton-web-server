# terraform/services/20-microservices/iam.tf

locals {
  iam_path    = "/delegatedadmin/developer/"
  name_prefix = "${local.app_prefix}-${local.workspace}"
}

# ============================================================================
# Assume Role Policy (shared)
# ============================================================================

data "aws_iam_policy_document" "ecs_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# ============================================================================
# Policy Documents
# ============================================================================

data "aws_iam_policy_document" "secrets" {
  statement {
    sid     = "AllowSecretsManagerAccess"
    actions = ["secretsmanager:GetSecretValue"]
    resources = [
      "arn:aws:secretsmanager:${local.region}:${local.account_id}:secret:/bb2/${local.workspace}/*",
      "arn:aws:secretsmanager:${local.region}:${local.account_id}:secret:/bb/${local.workspace}/*"
    ]
  }
}

data "aws_iam_policy_document" "ssm" {
  statement {
    sid = "AllowSSMAccess"
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters",
      "ssm:GetParametersByPath"
    ]
    resources = [
      "arn:aws:ssm:${local.region}:${local.account_id}:parameter/bb/${local.workspace}/*"
    ]
  }
}

data "aws_iam_policy_document" "kms" {
  count = local.kms_key_arn != null ? 1 : 0

  statement {
    sid       = "AllowKMSDecrypt"
    actions   = ["kms:Decrypt"]
    resources = [local.kms_key_arn]
  }
}

data "aws_iam_policy_document" "s3" {
  statement {
    sid     = "AllowS3Access"
    actions = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
    resources = [
      "arn:aws:s3:::${local.app_config_bucket}",
      "arn:aws:s3:::${local.app_config_bucket}/*",
      "arn:aws:s3:::bb-${local.bucket_env}-static-content",
      "arn:aws:s3:::bb-${local.bucket_env}-static-content/*"
    ]
  }
}

# ============================================================================
# IAM Policies
# ============================================================================

resource "aws_iam_policy" "secrets" {
  name   = "${local.name_prefix}-secrets"
  path   = local.iam_path
  policy = data.aws_iam_policy_document.secrets.json
}

resource "aws_iam_policy" "ssm" {
  name   = "${local.name_prefix}-ssm"
  path   = local.iam_path
  policy = data.aws_iam_policy_document.ssm.json
}

resource "aws_iam_policy" "kms" {
  count  = local.kms_key_arn != null ? 1 : 0
  name   = "${local.name_prefix}-kms"
  path   = local.iam_path
  policy = data.aws_iam_policy_document.kms[0].json
}

resource "aws_iam_policy" "s3" {
  name   = "${local.name_prefix}-s3"
  path   = local.iam_path
  policy = data.aws_iam_policy_document.s3.json
}

# ============================================================================
# Task Execution Role (ECS Agent: pull images, write logs, get secrets)
# ============================================================================

resource "aws_iam_role" "execution" {
  for_each = nonsensitive(local.service_config)

  name                 = "${local.name_prefix}-${each.key}-execution"
  path                 = local.iam_path
  assume_role_policy   = data.aws_iam_policy_document.ecs_assume_role.json
  permissions_boundary = local.permissions_boundary

  tags = { Name = "${local.name_prefix}-${each.key}" }
}

resource "aws_iam_role_policy_attachment" "execution_base" {
  for_each   = nonsensitive(local.service_config)
  role       = aws_iam_role.execution[each.key].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy_attachment" "execution_secrets" {
  for_each   = nonsensitive(local.service_config)
  role       = aws_iam_role.execution[each.key].name
  policy_arn = aws_iam_policy.secrets.arn
}

resource "aws_iam_role_policy_attachment" "execution_ssm" {
  for_each   = nonsensitive(local.service_config)
  role       = aws_iam_role.execution[each.key].name
  policy_arn = aws_iam_policy.ssm.arn
}

resource "aws_iam_role_policy_attachment" "execution_kms" {
  for_each   = local.kms_key_arn != null ? nonsensitive(local.service_config) : {}
  role       = aws_iam_role.execution[each.key].name
  policy_arn = aws_iam_policy.kms[0].arn
}

# ============================================================================
# Task Role (Container: runtime AWS access)
# ============================================================================

resource "aws_iam_role" "task" {
  for_each = nonsensitive(local.service_config)

  name                 = "${local.name_prefix}-${each.key}-task"
  path                 = local.iam_path
  assume_role_policy   = data.aws_iam_policy_document.ecs_assume_role.json
  permissions_boundary = local.permissions_boundary

  tags = { Name = "${local.name_prefix}-${each.key}" }
}

resource "aws_iam_role_policy_attachment" "task_secrets" {
  for_each   = nonsensitive(local.service_config)
  role       = aws_iam_role.task[each.key].name
  policy_arn = aws_iam_policy.secrets.arn
}

resource "aws_iam_role_policy_attachment" "task_ssm" {
  for_each   = nonsensitive(local.service_config)
  role       = aws_iam_role.task[each.key].name
  policy_arn = aws_iam_policy.ssm.arn
}

resource "aws_iam_role_policy_attachment" "task_kms" {
  for_each   = local.kms_key_arn != null ? nonsensitive(local.service_config) : {}
  role       = aws_iam_role.task[each.key].name
  policy_arn = aws_iam_policy.kms[0].arn
}

resource "aws_iam_role_policy_attachment" "task_s3" {
  for_each   = nonsensitive(local.service_config)
  role       = aws_iam_role.task[each.key].name
  policy_arn = aws_iam_policy.s3.arn
}
