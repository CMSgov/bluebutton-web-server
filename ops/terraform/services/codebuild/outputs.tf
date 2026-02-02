output "codebuild_project_name" {
  description = "Name of the CodeBuild project"
  value       = module.codebuild.project_name
}

output "codebuild_project_arn" {
  description = "ARN of the CodeBuild project"
  value       = module.codebuild.project_arn
  sensitive   = true
}

output "github_connection_arn" {
  description = "GitHub CodeStar connection ARN (confirm in AWS Console after first apply)"
  value       = module.codebuild.github_connection_arn
  sensitive   = true
}

output "ecr_repository_url" {
  description = "ECR repository URL for docker push"
  value       = aws_ecr_repository.api.repository_url
  sensitive   = true
}

output "github_actions_role_arn" {
  description = "IAM role ARN for GitHub Actions OIDC authentication"
  value       = aws_iam_role.github_actions.arn
  sensitive   = true
}
