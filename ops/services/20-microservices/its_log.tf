# ============================================================================
# its-log — standalone ECS service with its own task definition.
# Receives inbound traffic only from the BB api service (same cluster).
# Pulls its image from BCDA AWS account's ECR repo via the cross-account
# aws_ecr_repository_policy configured there. Deliberately does NOT reuse
# local.all_environment / local.all_secrets from main.tf — its-log gets only
# the minimal env vars and secrets it actually needs, sourced from its own Secrets Manager path.
# ============================================================================

locals {
  # BCDA AWS account — where the its-log ECR repo and cross-account IAM policies live.
  bcda_account_id = sensitive(data.aws_ssm_parameter.bcda_account_id.value)
  its_log_repo_name    = "cdap-its-log-sidecar"
  its_log_image_url    = "${local.bcda_account_id}.dkr.ecr.${local.region}.amazonaws.com/${local.its_log_repo_name}"
  its_log_repo_arn     = "arn:aws:ecr:${local.region}:${local.bcda_account_id}:repository/${local.its_log_repo_name}"

  its_log_cpu    = coalesce(try(var.service_overrides["its-log"].cpu, null), 256)
  its_log_memory = coalesce(try(var.service_overrides["its-log"].memory, null), 512)
  its_log_count  = coalesce(try(var.service_overrides["its-log"].count, null), 1)
  its_log_port   = coalesce(try(var.service_overrides["its-log"].port, null), 8080)
}

resource "aws_cloudwatch_log_group" "its_log" {
  name              = "/ecs/${local.app_prefix}-${local.workspace}-its-log"
  retention_in_days = var.log_retention_days
  kms_key_id        = local.kms_key_arn
  tags              = local.default_tags
}

# Inbound allowed only from the BB api service's security group, on its_log_port.
resource "aws_security_group" "its_log_sg" {
  name_prefix = "${local.app_prefix}-${local.workspace}-its-log-"
  description = "its-log service — inbound from api service only"
  vpc_id      = local.vpc_id

  ingress {
    description     = "Allow BB api service to reach its-log"
    from_port       = local.its_log_port
    to_port         = local.its_log_port
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_sg["api"].id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.app_prefix}-${local.workspace}-its-log-sg" }
}

resource "aws_iam_role" "its_log_execution" {
  name                 = "${local.app_prefix}-${local.workspace}-its-log-execution"
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

resource "aws_iam_role_policy" "its_log_execution_ecr" {
  name = "ecr-cross-account-pull"
  role = aws_iam_role.its_log_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ECRAuth"
        Effect   = "Allow"
        Action   = "ecr:GetAuthorizationToken"
        Resource = "*"
      },
      {
        Sid    = "ECRPullFromBCDAAccount"
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
        ]
        Resource = local.its_log_repo_arn
      }
    ]
  })
}

resource "aws_iam_role_policy" "its_log_execution_logs" {
  name = "cloudwatch-logs"
  role = aws_iam_role.its_log_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
      Resource = "${aws_cloudwatch_log_group.its_log.arn}:*"
    }]
  })
}

# Retrieve secrets in the same way BB API does, but with a different path so we don't
# grab all the secrets the main API has
data "aws_secretsmanager_secrets" "its_log_secrets" {
  filter {
    name   = "name"
    values = ["/bb2/${local.secrets_env}/its-log/"]
  }
}

data "aws_secretsmanager_secret" "its_log_secrets" {
  for_each = toset(data.aws_secretsmanager_secrets.its_log_secrets.arns)
  arn      = each.value
}

locals {
  its_log_secrets_discovered = [
    for secret in data.aws_secretsmanager_secret.its_log_secrets : {
      name      = upper(replace(basename(secret.name), "-", "_"))
      valueFrom = secret.arn
    }
  ]

  its_log_all_secrets = local.its_log_secrets_discovered
}

resource "aws_iam_role_policy" "its_log_execution_secrets" {
  name = "secrets-manager-sensitive"
  role = aws_iam_role.its_log_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "SecretsManagerGetSecretValue"
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = "arn:aws:secretsmanager:${local.region}:${data.aws_caller_identity.current.account_id}:secret:/bb2/${local.secrets_env}/its-log/*"
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

resource "aws_iam_role" "its_log_task" {
  name                 = "${local.app_prefix}-${local.workspace}-its-log-task"
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

# ----------------------------------------------------------------------------
# EFS — persistent storage for its-log output.
# ----------------------------------------------------------------------------
resource "aws_efs_file_system" "its_log" {
  creation_token   = "${local.app_prefix}-${local.workspace}-its-log"
  encrypted        = true
  kms_key_id       = local.kms_key_arn
  performance_mode = "generalPurpose"
  throughput_mode  = "bursting"

  lifecycle_policy {
    transition_to_ia = "AFTER_30_DAYS"
  }

  tags = { Name = "${local.app_prefix}-${local.workspace}-its-log-efs" }
}

resource "aws_security_group" "its_log_efs_sg" {
  name_prefix = "${local.app_prefix}-${local.workspace}-its-log-efs-"
  description = "its-log EFS mount targets — inbound NFS from its-log task only"
  vpc_id      = local.vpc_id

  ingress {
    description     = "Allow its-log task to mount EFS"
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [aws_security_group.its_log_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.app_prefix}-${local.workspace}-its-log-efs-sg" }
}

resource "aws_efs_mount_target" "its_log" {
  for_each        = toset(local.private_subnets)
  file_system_id  = aws_efs_file_system.its_log.id
  subnet_id       = each.value
  security_groups = [aws_security_group.its_log_efs_sg.id]
}

resource "aws_efs_access_point" "its_log" {
  file_system_id = aws_efs_file_system.its_log.id

  posix_user {
    # TODO: Change if the uid in the its-log container is different than the default of 1000
    uid = 1000
    gid = 1000
  }

  root_directory {
    path = "/its-log"
    creation_info {
      # TODO: Change if the uid in the its-log container is different than the default of 1000
      owner_uid   = 1000
      owner_gid   = 1000
      permissions = "750"
    }
  }

  tags = { Name = "${local.app_prefix}-${local.workspace}-its-log-ap" }
}

resource "aws_iam_role_policy" "its_log_task_efs" {
  name = "efs-access"
  role = aws_iam_role.its_log_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AllowEFSClientAccess"
      Effect = "Allow"
      Action = [
        "elasticfilesystem:ClientMount",
        "elasticfilesystem:ClientWrite",
      ]
      Resource = aws_efs_file_system.its_log.arn
      Condition = {
        StringEquals = {
          "elasticfilesystem:AccessPointArn" = aws_efs_access_point.its_log.arn
        }
      }
    }]
  })
}

# ----------------------------------------------------------------------------
# Task definition and service
# ----------------------------------------------------------------------------
resource "aws_ecs_task_definition" "its_log" {
  family = "${local.app_prefix}-${local.workspace}-its-log-family"

  container_definitions = jsonencode([{
    name      = "its-log"
    image     = "${local.its_log_image_url}:${var.its_log_image_tag}"
    essential = true

    readonlyRootFilesystem = true

    portMappings = [{
      containerPort = local.its_log_port
      protocol      = "tcp"
    }]

    mountPoints = [{
      sourceVolume  = "its-log-efs"
      # TODO: Modify this based on where we actually end up writing to in its-log, something like "/app/its-log/api/data"
      containerPath = "/mnt/its-log"
      readOnly      = false
    }]

    environment = var.its_log_environment_variables
    secrets     = local.its_log_all_secrets

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.its_log.name
        "awslogs-region"        = data.aws_region.current.region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])

  task_role_arn            = aws_iam_role.its_log_task.arn
  execution_role_arn       = aws_iam_role.its_log_execution.arn
  network_mode             = "awsvpc"
  cpu                      = local.its_log_cpu
  memory                   = local.its_log_memory
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

  tags = { Name = "${local.app_prefix}-${local.workspace}-its-log-task" }
}

resource "aws_ecs_service" "its_log" {
  name                    = "${local.app_prefix}-${local.workspace}-its-log-service"
  cluster                 = data.aws_ecs_cluster.main.arn
  task_definition         = aws_ecs_task_definition.its_log.arn
  desired_count           = local.its_log_count
  enable_execute_command  = true
  launch_type             = "FARGATE"
  platform_version        = "LATEST"

  network_configuration {
    assign_public_ip = false
    subnets          = local.private_subnets
    security_groups  = [aws_security_group.its_log_sg.id]
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  lifecycle {
    ignore_changes = [desired_count, task_definition]
  }

  tags = { Name = "${local.app_prefix}-${local.workspace}-its-log-service" }
}