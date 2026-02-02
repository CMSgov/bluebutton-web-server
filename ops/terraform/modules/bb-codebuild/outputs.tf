# Outputs for bb-codebuild module

output "project_name" {
  description = "Name of the CodeBuild project"
  value       = aws_codebuild_project.main.name
}

output "project_arn" {
  description = "ARN of the CodeBuild project"
  value       = aws_codebuild_project.main.arn
  sensitive   = true
}

output "github_connection_arn" {
  description = "ARN of GitHub CodeStar connection (must be confirmed in AWS Console after first apply)"
  value       = aws_codestarconnections_connection.github.arn
  sensitive   = true
}

output "iam_role_arn" {
  description = "ARN of the CodeBuild IAM role"
  value       = aws_iam_role.codebuild.arn
  sensitive   = true
}

output "log_group_name" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.runner.name
}
