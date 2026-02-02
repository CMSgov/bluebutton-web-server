# terraform/modules/bb-ecs/sg.tf
# Updated to use platform object

# Security Group for ECS Tasks
resource "aws_security_group" "ecs_sg" {
  for_each    = nonsensitive(local.service_config)
  name        = "${local.app_prefix}-${local.workspace}-ecs-${each.key}-sg"
  description = "ECS ${title(each.key)} Security Group"
  vpc_id      = var.platform.vpc_id

  tags = merge(local.common_tags, {
    Name = "${local.app_prefix}-${local.workspace}-${each.key}-ecs-sg"
  })

  # Allow from ALB
  dynamic "ingress" {
    for_each = each.value.alb ? [1] : []
    content {
      description     = "Allow port ${each.value.port} from ${title(each.key)} ALB Security Group"
      from_port       = each.value.port
      to_port         = each.value.port
      protocol        = "tcp"
      security_groups = [aws_security_group.alb_sg[each.key].id]
    }
  }

  # Allow from private subnets
  ingress {
    description = "Allow port ${each.value.port} from Private Subnets"
    from_port   = each.value.port
    to_port     = each.value.port
    protocol    = "tcp"
    cidr_blocks = [for id, sub in var.platform.private_subnets : sub.cidr_block]
  }

  egress {
    description = "Allow all traffic outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Security Group for ALB
resource "aws_security_group" "alb_sg" {
  for_each    = nonsensitive({ for k, v in local.service_config : k => v if v.alb })
  name        = "${local.app_prefix}-${local.workspace}-${each.key}-alb-sg"
  description = "ALB ${title(each.key)} Security Group"
  vpc_id      = var.platform.vpc_id

  tags = merge(local.common_tags, {
    Name = "${local.app_prefix}-${local.workspace}-${each.key}-alb-sg"
  })

  ingress {
    description = "HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all traffic outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
