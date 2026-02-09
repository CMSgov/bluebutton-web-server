# terraform/services/20-microservices/security_groups.tf
# Separate rule resources following BFD/AB2D pattern

# ============================================================================
# Security Group for ECS Tasks (empty shell — rules defined separately)
# ============================================================================
resource "aws_security_group" "ecs_sg" {
  for_each    = nonsensitive(local.service_config)
  name        = "${local.app_prefix}-${local.workspace}-ecs-${each.key}-sg"
  description = "ECS ${title(each.key)} Security Group"
  vpc_id      = local.platform.vpc_id

  tags = merge(local.common_tags, {
    Name = "${local.app_prefix}-${local.workspace}-${each.key}-ecs-sg"
  })
}

# ECS ingress: Allow from ALB
resource "aws_vpc_security_group_ingress_rule" "ecs_from_alb" {
  for_each = nonsensitive({ for k, v in local.service_config : k => v if v.alb })

  security_group_id            = aws_security_group.ecs_sg[each.key].id
  referenced_security_group_id = aws_security_group.alb_sg[each.key].id
  from_port                    = each.value.port
  to_port                      = each.value.port
  ip_protocol                  = "tcp"
  description                  = "Allow port ${each.value.port} from ${title(each.key)} ALB"
}

# ECS ingress: Allow from each private subnet CIDR
resource "aws_vpc_security_group_ingress_rule" "ecs_from_private" {
  for_each = {
    for pair in flatten([
      for svc_key, svc in nonsensitive(local.service_config) : [
        for subnet_id, subnet in local.platform.private_subnets : {
          key       = "${svc_key}-${subnet_id}"
          svc_key   = svc_key
          port      = svc.port
          cidr_ipv4 = subnet.cidr_block
        }
      ]
    ]) : pair.key => pair
  }

  security_group_id = aws_security_group.ecs_sg[each.value.svc_key].id
  cidr_ipv4         = each.value.cidr_ipv4
  from_port         = each.value.port
  to_port           = each.value.port
  ip_protocol       = "tcp"
  description       = "Allow from private subnet ${each.value.cidr_ipv4}"
}

# ECS egress: Allow all outbound
resource "aws_vpc_security_group_egress_rule" "ecs_all" {
  for_each = nonsensitive(local.service_config)

  security_group_id = aws_security_group.ecs_sg[each.key].id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Allow all outbound"
}

# ============================================================================
# Security Group for ALB (empty shell — rules defined separately)
# ============================================================================
resource "aws_security_group" "alb_sg" {
  for_each    = nonsensitive({ for k, v in local.service_config : k => v if v.alb })
  name        = "${local.app_prefix}-${local.workspace}-${each.key}-alb-sg"
  description = "ALB ${title(each.key)} Security Group"
  vpc_id      = local.platform.vpc_id

  tags = merge(local.common_tags, {
    Name = "${local.app_prefix}-${local.workspace}-${each.key}-alb-sg"
  })
}

# ALB ingress: HTTPS from anywhere (dev/test only)
resource "aws_vpc_security_group_ingress_rule" "alb_https_open" {
  for_each = var.alb_allow_all_ingress ? nonsensitive({ for k, v in local.service_config : k => v if v.alb }) : {}

  security_group_id = aws_security_group.alb_sg[each.key].id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
  description       = "HTTPS from anywhere"
}

# ALB ingress: HTTPS from VPN/CDN security groups (restricted mode)
resource "aws_vpc_security_group_ingress_rule" "alb_from_vpn" {
  for_each = !var.alb_allow_all_ingress ? nonsensitive({ for k, v in local.service_config : k => v if v.alb }) : {}

  security_group_id            = aws_security_group.alb_sg[each.key].id
  referenced_security_group_id = data.aws_security_group.cmscloud_vpn.id
  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
  description                  = "HTTPS from cmscloud-vpn"
}

resource "aws_vpc_security_group_ingress_rule" "alb_from_cms_vpn" {
  for_each = !var.alb_allow_all_ingress ? nonsensitive({ for k, v in local.service_config : k => v if v.alb }) : {}

  security_group_id            = aws_security_group.alb_sg[each.key].id
  referenced_security_group_id = data.aws_security_group.clb_cms_vpn.id
  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
  description                  = "HTTPS from clb-cms-vpn"
}

resource "aws_vpc_security_group_ingress_rule" "alb_from_akamai" {
  for_each = !var.alb_allow_all_ingress ? nonsensitive({ for k, v in local.service_config : k => v if v.alb }) : {}

  security_group_id            = aws_security_group.alb_sg[each.key].id
  referenced_security_group_id = data.aws_security_group.clb_akamai.id
  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
  description                  = "HTTPS from clb-akamai-prod"
}

# ALB ingress: Additional security groups (if any)
resource "aws_vpc_security_group_ingress_rule" "alb_from_additional" {
  for_each = {
    for pair in flatten([
      for svc_key, svc in nonsensitive({ for k, v in local.service_config : k => v if v.alb }) : [
        for idx, sg_id in var.alb_security_group_ids : {
          key     = "${svc_key}-additional-${idx}"
          svc_key = svc_key
          sg_id   = sg_id
        }
      ]
    ]) : pair.key => pair
    if !var.alb_allow_all_ingress
  }

  security_group_id            = aws_security_group.alb_sg[each.value.svc_key].id
  referenced_security_group_id = each.value.sg_id
  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
  description                  = "HTTPS from additional security group"
}

# ALB egress: Allow all outbound
resource "aws_vpc_security_group_egress_rule" "alb_all" {
  for_each = nonsensitive({ for k, v in local.service_config : k => v if v.alb })

  security_group_id = aws_security_group.alb_sg[each.key].id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Allow all outbound"
}

