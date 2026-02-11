# terraform/services/20-microservices/outputs.tf

output "cluster_name" {
  description = "ECS cluster name"
  value       = data.aws_ecs_cluster.main.cluster_name
}

output "cluster_arn" {
  description = "ECS cluster ARN"
  value       = data.aws_ecs_cluster.main.arn
  sensitive   = true
}

output "service_names" {
  description = "ECS service names"
  value       = { for k, v in aws_ecs_service.ecs_service : k => v.name }
}

output "ecr_repository_url" {
  description = "ECR repository URL from bootstrap"
  value       = local.ecr_repository_url
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

output "ssm_service_configs" {
  description = "Parsed service configuration from SSM JSON"
  sensitive   = true
  value       = local.ssm_service_configs
}
