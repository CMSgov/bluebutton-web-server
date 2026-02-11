# ops/modules/sops/outputs.tf

output "sopsw" {
  description = "Command to edit the current environment's encrypted values file"
  value       = var.create_sopsw_wrapper ? "${local_file.sopsw[0].filename} -e ${local.values_file_path}" : null
}

output "ssm_parameters" {
  description = "Map of provisioned SSM parameter names to their ARNs"
  sensitive   = true
  value       = { for k, v in aws_ssm_parameter.this : k => v.arn }
}

output "parameter_count" {
  description = "Number of SSM parameters provisioned"
  value       = length(aws_ssm_parameter.this)
}
