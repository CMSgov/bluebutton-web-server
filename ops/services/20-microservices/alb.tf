# terraform/modules/bb-ecs/alb.tf
# Updated to use platform object

# Application Load Balancer
resource "aws_lb" "alb" {
  for_each           = nonsensitive({ for k, v in local.service_config : k => v if v.alb })
  name               = "${local.app_prefix}-${local.workspace}-${each.key}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg[each.key].id]
  subnets            = local.public_subnets

  enable_deletion_protection = var.enable_deletion_protection

  access_logs {
    bucket  = var.access_logs_bucket != "" ? var.access_logs_bucket : "cms-cloud-${local.account_id}-${local.region}"
    prefix  = "${local.app_prefix}-${local.workspace}-${each.key}"
    enabled = var.enable_access_logs
  }

  tags = merge(local.common_tags, {
    Name = "${local.app_prefix}-${local.workspace}-${each.key}-alb"
  })
}

# Target Group
resource "aws_lb_target_group" "tg" {
  for_each    = nonsensitive({ for k, v in local.service_config : k => v if v.alb })
  name        = "${local.app_prefix}-${local.workspace}-${each.key}-tg"
  port        = each.value.port
  protocol    = "HTTP"
  vpc_id      = local.platform.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = each.value.health_check_path
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 3
  }

  tags = merge(local.common_tags, {
    Name = "${local.app_prefix}-${local.workspace}-${each.key}-tg"
  })
}

# HTTPS Listener
resource "aws_lb_listener" "https" {
  for_each          = nonsensitive({ for k, v in local.service_config : k => v if v.alb })
  load_balancer_arn = aws_lb.alb[each.key].arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = local.platform.acm_certificate != null ? local.platform.acm_certificate.arn : null

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg[each.key].arn
  }

  tags = local.common_tags
}

