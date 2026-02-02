# terraform/modules/bb-ecs/iam.tf
# Updated to use platform object

# Task Execution Role (for ECS to pull images and write logs)
resource "aws_iam_role" "task_execution" {
  for_each = nonsensitive(local.service_config)
  name     = "${local.app_prefix}-${local.workspace}-${each.key}-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  # Use permissions boundary if available
  permissions_boundary = var.platform.permissions_boundary

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "task_execution" {
  for_each   = nonsensitive(local.service_config)
  role       = aws_iam_role.task_execution[each.key].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Policy for Secrets Manager access
resource "aws_iam_role_policy" "task_execution_secrets" {
  for_each = nonsensitive(local.service_config)
  name     = "${local.app_prefix}-${local.workspace}-${each.key}-secrets-policy"
  role     = aws_iam_role.task_execution[each.key].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = "arn:aws:secretsmanager:${local.region}:${local.account_id}:secret:/bb2/${local.workspace}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameters",
          "ssm:GetParameter"
        ]
        Resource = "arn:aws:ssm:${local.region}:${local.account_id}:parameter/bluebutton/${local.workspace}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["kms:Decrypt"]
        Resource = var.platform.kms_alias != null ? var.platform.kms_alias.target_key_arn : "*"
      }
    ]
  })
}

# Task Role (for the container to access AWS services)
resource "aws_iam_role" "task" {
  for_each = nonsensitive(local.service_config)
  name     = "${local.app_prefix}-${local.workspace}-${each.key}-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  # Use permissions boundary if available
  permissions_boundary = var.platform.permissions_boundary

  tags = local.common_tags
}

resource "aws_iam_role_policy" "task" {
  for_each = nonsensitive(local.service_config)
  name     = "${local.app_prefix}-${local.workspace}-${each.key}-task-policy"
  role     = aws_iam_role.task[each.key].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.app_config_bucket}",
          "arn:aws:s3:::${var.app_config_bucket}/*",
          "arn:aws:s3:::${var.static_content_bucket}",
          "arn:aws:s3:::${var.static_content_bucket}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = "arn:aws:secretsmanager:${local.region}:${local.account_id}:secret:/bb2/${local.workspace}/*"
      }
    ]
  })
}
