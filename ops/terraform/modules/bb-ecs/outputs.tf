# terraform/modules/bb-ecs/outputs.tf

output "cluster_name" {
  description = "ECS cluster name"
  value       = local.cluster_name
}

output "cluster_arn" {
  description = "ECS cluster ARN"
  value       = var.create_cluster ? aws_ecs_cluster.cluster[0].arn : data.aws_ecs_cluster.existing[0].arn
  sensitive   = true
}

output "service_names" {
  description = "ECS service names"
  value       = { for k, v in aws_ecs_service.ecs_service : k => v.name }
}

output "ecr_repository_urls" {
  description = "ECR repository URLs"
  value       = { for k, v in aws_ecr_repository.repo : k => v.repository_url }
  sensitive   = true
}

output "alb_dns_names" {
  description = "ALB DNS names"
  value       = { for k, v in aws_lb.alb : k => v.dns_name }
}

output "alb_zone_ids" {
  description = "ALB Route 53 zone IDs"
  value       = { for k, v in aws_lb.alb : k => v.zone_id }
}

output "target_group_arns" {
  description = "Target group ARNs"
  value       = { for k, v in aws_lb_target_group.tg : k => v.arn }
  sensitive   = true
}

output "ecs_security_group_ids" {
  description = "ECS task security group IDs"
  value       = { for k, v in aws_security_group.ecs_sg : k => v.id }
  sensitive   = true
}

output "log_group_names" {
  description = "CloudWatch log group names"
  value       = { for k, v in aws_cloudwatch_log_group.ecs : k => v.name }
}

output "ssm_config" {
  description = "Parameter:Value map of loaded SSM configuration"
  sensitive   = true
  value       = local.ssm_config
}
