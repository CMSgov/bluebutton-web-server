# Platform outputs
output "environment" {
  description = "Deployed environment"
  value       = module.platform.env
}

output "parent_env" {
  description = "Parent environment"
  value       = module.platform.parent_env
}

output "workspace" {
  description = "OpenTofu workspace"
  value       = terraform.workspace
}

# ECS outputs
output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.bb_ecs.cluster_name
}

output "ecs_service_names" {
  description = "ECS service names"
  value       = module.bb_ecs.service_names
}

output "ecr_repository_urls" {
  description = "ECR repository URLs"
  sensitive   = true
  value       = module.bb_ecs.ecr_repository_urls
}

# ALB outputs
output "alb_dns_names" {
  description = "ALB DNS names"
  value       = module.bb_ecs.alb_dns_names
}

# Network outputs
output "vpc_id" {
  description = "VPC ID"
  sensitive   = true
  value       = module.platform.vpc_id
}

# SNS outputs
output "sns_topic_arn" {
  description = "CloudWatch alarms SNS topic ARN"
  value       = aws_sns_topic.cloudwatch_alarms_topic.arn
}

# CodeBuild outputs
output "codebuild_ecr_repository_url" {
  description = "ECR repository URL for pushing images"
  value       = module.codebuild.ecr_repository_url
}

output "github_actions_role_arn" {
  description = "ARN of the GitHub Actions IAM role"
  value       = module.codebuild.github_actions_role_arn
}

output "codebuild_project_name" {
  description = "CodeBuild project name (use in workflow runs-on label)"
  value       = module.codebuild.project_name
}
