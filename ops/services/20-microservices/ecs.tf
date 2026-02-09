# terraform/services/20-microservices/ecs.tf
# Note: ECS Cluster is managed by 10-cluster service and referenced via data source

# ECS Task Definition
resource "aws_ecs_task_definition" "ecs_task" {
  for_each = nonsensitive(local.service_config)
  family   = "${local.app_prefix}-${local.workspace}-${each.key}-family"

  # Using jsonencode instead of templatefile for better maintainability
  container_definitions = jsonencode([{
    name      = "${local.app_prefix}-${local.workspace}-${each.key}"
    image     = "${local.ecr_repository_url}:${var.image_tag}"
    essential = true

    readonlyRootFilesystem = true

    portMappings = [{
      containerPort = each.value.port
      protocol      = "tcp"
    }]

    mountPoints = [
      { containerPath = "/tmp", sourceVolume = "tmp", readOnly = false }
    ]

    environment = local.all_environment
    secrets     = local.all_secrets
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.ecs[each.key].name
        "awslogs-region"        = data.aws_region.current.id
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])

  volume {
    name = "tmp"
  }

  task_role_arn            = aws_iam_role.task[each.key].arn
  execution_role_arn       = aws_iam_role.execution[each.key].arn
  network_mode             = "awsvpc"
  cpu                      = each.value.cpu
  memory                   = each.value.memory
  requires_compatibilities = ["FARGATE"]

  tags = merge(local.common_tags, {
    Name = "${local.app_prefix}-${local.workspace}-${each.key}-task"
  })
}

# ECS Service
resource "aws_ecs_service" "ecs_service" {
  for_each               = nonsensitive(local.service_config)
  name                   = "${local.app_prefix}-${local.workspace}-${each.key}-service"
  cluster                = data.aws_ecs_cluster.main.arn
  task_definition        = aws_ecs_task_definition.ecs_task[each.key].arn
  desired_count          = each.value.count
  enable_execute_command = true
  launch_type            = "FARGATE"
  platform_version       = "LATEST"

  network_configuration {
    assign_public_ip = false
    subnets          = local.private_subnets
    security_groups  = [aws_security_group.ecs_sg[each.key].id]
  }

  # Attach to ALB if enabled
  dynamic "load_balancer" {
    for_each = each.value.alb ? [1] : []
    content {
      target_group_arn = aws_lb_target_group.tg[each.key].arn
      container_name   = "${local.app_prefix}-${local.workspace}-${each.key}"
      container_port   = each.value.port
    }
  }

  # Give containers time to start before health checks fail them
  health_check_grace_period_seconds = each.value.alb ? 60 : null

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  lifecycle {
    ignore_changes = [desired_count]
  }

  tags = merge(local.common_tags, {
    Name = "${local.app_prefix}-${local.workspace}-${each.key}-service"
  })
}

# Auto Scaling Target
resource "aws_appautoscaling_target" "ecs_autoscale" {
  for_each           = nonsensitive({ for k, v in local.service_config : k => v if v.autoscale_enabled })
  max_capacity       = each.value.max_capacity
  min_capacity       = each.value.min_capacity
  resource_id        = "service/${local.cluster_name}/${aws_ecs_service.ecs_service[each.key].name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# Auto Scaling Policy - CPU
resource "aws_appautoscaling_policy" "ecs_cpu_policy" {
  for_each           = nonsensitive({ for k, v in local.service_config : k => v if v.autoscale_enabled })
  name               = "scale_on_cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_autoscale[each.key].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_autoscale[each.key].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_autoscale[each.key].service_namespace

  target_tracking_scaling_policy_configuration {
    target_value = var.cpu_target_value
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}

# Auto Scaling Policy - Memory
resource "aws_appautoscaling_policy" "ecs_memory_policy" {
  for_each           = nonsensitive({ for k, v in local.service_config : k => v if v.autoscale_enabled })
  name               = "scale_on_mem"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_autoscale[each.key].resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_autoscale[each.key].scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_autoscale[each.key].service_namespace

  target_tracking_scaling_policy_configuration {
    target_value = var.memory_target_value
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
  }
}
