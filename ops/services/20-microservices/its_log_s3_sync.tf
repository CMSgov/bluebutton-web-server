# ============================================================================
# its-log → shared export bucket (bb-{{env}}-aurora-export)
# Scheduled Fargate task that mounts the its-log EFS access point read-only
# and syncs its contents to the shared aurora_export bucket in cdap-prod.
# Cross-account access is granted inside the cdap repository
# registry (KMS) and a bucket policy write statement (S3) — both owned and
# applied in the cdap-prod account, not here. Need to coordinate with them once we have the role ARN
# ============================================================================

locals {
  # modules/bucket uses bucket_prefix, so the deployed bucket name carries an
  # AWS-generated random suffix we can't know at plan time — match by prefix.
  its_log_export_bucket_arn_pattern = "arn:aws:s3:::bb-prod-aurora-export-*"
}

data "aws_secretsmanager_secret" "its_log_export_bucket_name" {
  name = "bb2/${local.secrets_env}/its-log-s3-sync/bucket-name"
}

resource "aws_cloudwatch_log_group" "its_log_s3_sync" {
  name              = "/ecs/${local.app_prefix}-${local.workspace}-its-log-s3-sync"
  retention_in_days = var.log_retention_days
  kms_key_id        = local.kms_key_arn
  tags              = local.default_tags
}

resource "aws_iam_role" "its_log_s3_sync_execution" {
  name                 = "${local.app_prefix}-${local.workspace}-its-log-s3-sync-execution"
  permissions_boundary = local.permissions_boundary

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = local.default_tags
}

resource "aws_iam_role_policy" "its_log_s3_sync_execution_logs" {
  name = "cloudwatch-logs"
  role = aws_iam_role.its_log_s3_sync_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
      Resource = "${aws_cloudwatch_log_group.its_log_s3_sync.arn}:*"
    }]
  })
}

# This role's ARN will need to be shared with CDAP to enable the write permissions policy
# on the s3 bucket where the its-log CSVs will ultimately end up
resource "aws_iam_role" "its_log_s3_sync_task" {
  name                 = "${local.app_prefix}-${local.workspace}-its-log-s3-sync-task"
  permissions_boundary = local.permissions_boundary

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = local.default_tags
}

# Read-only EFS access
resource "aws_iam_role_policy" "its_log_s3_sync_task_efs" {
  name = "efs-read-access"
  role = aws_iam_role.its_log_s3_sync_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid      = "AllowEFSClientMount"
      Effect   = "Allow"
      Action   = ["elasticfilesystem:ClientMount"]
      Resource = aws_efs_file_system.its_log.arn
      Condition = {
        StringEquals = {
          "elasticfilesystem:AccessPointArn" = aws_efs_access_point.its_log.arn
        }
      }
    }]
  })
}

# S3 + KMS — these only take effect once BCDA's bucket policy and the
# aurora_export key policy both name this role. Identity-based (here) and
# resource-based (BCDA's side) grants have to agree on both sides.
resource "aws_iam_role_policy" "its_log_s3_sync_task_s3" {
  name = "s3-export-bucket-write"
  role = aws_iam_role.its_log_s3_sync_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ListExportBucket"
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = local.its_log_export_bucket_arn_pattern
      },
      {
        Sid      = "WriteExportObjects"
        Effect   = "Allow"
        Action   = ["s3:PutObject"]
        Resource = "${local.its_log_export_bucket_arn_pattern}/*"
      },
      {
        Sid    = "EncryptExportObjects"
        Effect = "Allow"
        Action = [
          "kms:Encrypt",
          "kms:GenerateDataKey",
          "kms:DescribeKey",
        ]
        Resource = "arn:aws:kms:us-east-1:${local.bcda_account_id}:key/*"
        Condition = {
          "ForAnyValue:StringEquals" = {
            "kms:ResourceAliases" = ["alias/aurora_export"]
          }
        }
      }
    ]
  })
}

# Policy to allow the s3 sync role to retrieve the BCDA bucket name from secrets manager
resource "aws_iam_role_policy" "its_log_s3_sync_execution_secrets" {
  name = "secrets-manager-bucket-name"
  role = aws_iam_role.its_log_s3_sync_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "GetBucketNameSecret"
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = data.aws_secretsmanager_secret.its_log_export_bucket_name.arn
      },
      {
        Sid      = "KMSDecrypt"
        Effect   = "Allow"
        Action   = ["kms:Decrypt"]
        Resource = local.kms_key_arn
      }
    ]
  })
}

resource "aws_ecs_task_definition" "its_log_s3_sync" {
  family = "${local.app_prefix}-${local.workspace}-its-log-s3-sync-family"

  container_definitions = jsonencode([{
    name      = "its-log-s3-sync"
    image     = "public.ecr.aws/aws-cli/aws-cli:latest"
    essential = true

    entryPoint = ["sh", "-c"]
    command = [
      "aws s3 sync /mnt/its-log s3://$AURORA_EXPORT_BUCKET_NAME/ --delete"
    ]

    readonlyRootFilesystem = false

    mountPoints = [{
      sourceVolume  = "its-log-efs"
      containerPath = "/mnt/its-log"
      readOnly      = true
    }]

    secrets = [
      {
        name      = "AURORA_EXPORT_BUCKET_NAME"
        valueFrom = data.aws_secretsmanager_secret.its_log_export_bucket_name.arn
      }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.its_log_s3_sync.name
        "awslogs-region"        = data.aws_region.current.region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])

  task_role_arn            = aws_iam_role.its_log_s3_sync_task.arn
  execution_role_arn       = aws_iam_role.its_log_s3_sync_execution.arn
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  requires_compatibilities = ["FARGATE"]

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "ARM64"
  }

  volume {
    name = "its-log-efs"

    efs_volume_configuration {
      file_system_id     = aws_efs_file_system.its_log.id
      transit_encryption = "ENABLED"

      authorization_config {
        access_point_id = aws_efs_access_point.its_log.id
        iam             = "ENABLED"
      }
    }
  }

  tags = { Name = "${local.app_prefix}-${local.workspace}-its-log-s3-sync-task" }
}

# EventBridge scheduler to launch the s3sync
resource "aws_iam_role" "its_log_s3_sync_scheduler" {
  name                 = "${local.app_prefix}-${local.workspace}-its-log-s3-sync-scheduler"
  permissions_boundary = local.permissions_boundary

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "scheduler.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = local.default_tags
}

resource "aws_iam_role_policy" "its_log_s3_sync_scheduler_run_task" {
  name = "run-ecs-task"
  role = aws_iam_role.its_log_s3_sync_scheduler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "RunTask"
        Effect   = "Allow"
        Action   = "ecs:RunTask"
        Resource = "${replace(aws_ecs_task_definition.its_log_s3_sync.arn, "/:[0-9]+$/", "")}:*"
        Condition = {
          ArnLike = { "ecs:cluster" = data.aws_ecs_cluster.main.arn }
        }
      },
      {
        Sid    = "PassRoles"
        Effect = "Allow"
        Action = "iam:PassRole"
        Resource = [
          aws_iam_role.its_log_s3_sync_execution.arn,
          aws_iam_role.its_log_s3_sync_task.arn,
        ]
      }
    ]
  })
}

resource "aws_scheduler_schedule" "its_log_s3_sync" {
  name                          = "${local.app_prefix}-${local.workspace}-its-log-s3-sync"
  schedule_expression           = var.its_log_s3_sync_schedule
  schedule_expression_timezone  = "UTC"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = data.aws_ecs_cluster.main.arn
    role_arn = aws_iam_role.its_log_s3_sync_scheduler.arn

    ecs_parameters {
      task_definition_arn = aws_ecs_task_definition.its_log_s3_sync.arn
      launch_type          = "FARGATE"
      platform_version     = "LATEST"

      network_configuration {
        subnets          = local.private_subnets
        security_groups  = [aws_security_group.its_log_sg.id]
        assign_public_ip = false
      }
    }
  }
}

# We will need to hand this off or work with the CDAP team, so this ARN can be applied
# and given write permissions to the bb-{{ENV}}-aurora-export s3 bucket
output "its_log_s3_sync_task_role_arn" {
  value       = aws_iam_role.its_log_s3_sync_task.arn
  description = "Role ARN to register in cdap-prod's kms_shares and bucket policy for its-log S3 sync write access."
}