# Bootstrap Outputs

# Environment KMS Key Outputs (pre-existing key)
output "env_kms_key_arn" {
  description = "ARN of the environment KMS key"
  value       = data.aws_kms_alias.env.target_key_arn
  sensitive   = true
}

output "env_kms_key_alias" {
  description = "Alias of the environment KMS key"
  value       = data.aws_kms_alias.env.name
}

# ECR Outputs
output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = local.create_resources ? aws_ecr_repository.api[0].repository_url : null
}

output "ecr_repository_arn" {
  description = "ARN of the ECR repository"
  value       = local.create_resources ? aws_ecr_repository.api[0].arn : null
}

output "ecr_kms_key_arn" {
  description = "ARN of the KMS key used for ECR encryption"
  value       = local.create_resources ? aws_kms_key.ecr[0].arn : null
  sensitive   = true
}

# CodeBuild Outputs
output "codebuild_project_arn" {
  description = "ARN of the CodeBuild project"
  value       = local.create_resources ? aws_codebuild_project.main[0].arn : null
}

output "codebuild_project_name" {
  description = "Name of the CodeBuild project"
  value       = local.create_resources ? aws_codebuild_project.main[0].name : null
}

output "codebuild_role_arn" {
  description = "ARN of the CodeBuild service role"
  value       = local.create_resources ? aws_iam_role.codebuild[0].arn : null
  sensitive   = true
}

# GitHub OIDC Outputs
output "github_oidc_provider_arn" {
  description = "ARN of GitHub Actions OIDC provider"
  value       = local.create_resources ? aws_iam_openid_connect_provider.github_actions[0].arn : "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/token.actions.githubusercontent.com"
  sensitive   = true
}

output "github_actions_role_arn" {
  description = "ARN of GitHub Actions deployment role"
  value       = aws_iam_role.github_actions.arn
  sensitive   = true
}

output "github_actions_role_name" {
  description = "Name of GitHub Actions deployment role"
  value       = aws_iam_role.github_actions.name
}

# GitHub Connection Output
output "github_connection_arn" {
  description = "ARN of the GitHub CodeStar connection"
  value       = local.create_resources ? aws_codestarconnections_connection.github[0].arn : null
  sensitive   = true
}
