# Outputs for bb-codebuild module

output "project_name" {
  description = "Name of the CodeBuild project"
  value       = aws_codebuild_project.main.name
}

output "project_arn" {
  description = "ARN of the CodeBuild project"
  value       = aws_codebuild_project.main.arn
}

output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.api.repository_url
}

output "ecr_repository_arn" {
  description = "ARN of the ECR repository"
  value       = aws_ecr_repository.api.arn
}

output "github_actions_role_arn" {
  description = "ARN of the GitHub Actions IAM role (for OIDC)"
  value       = aws_iam_role.github_actions.arn
}

output "github_connection_arn" {
  description = "ARN of the GitHub CodeStar connection"
  value       = aws_codestarconnections_connection.github.arn
}

output "codebuild_role_arn" {
  description = "ARN of the CodeBuild service role"
  value       = aws_iam_role.codebuild.arn
}
