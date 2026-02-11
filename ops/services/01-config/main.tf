# ops/services/01-config/main.tf
# SOPS-managed configuration service — decrypts sopsw files and provisions SSM parameters

locals {
  env          = terraform.workspace
  service      = "config"
  default_tags = module.platform.default_tags
}

module "platform" {
  source    = "../../modules/platform"
  providers = { aws = aws, aws.secondary = aws.secondary }

  app           = local.app
  env           = local.env
  service       = local.service
  root_module   = "https://github.com/CMSgov/bluebutton-web-server/tree/main/ops/services/01-config"
  kms_key_alias = "alias/bb-${local.env}-app-key-alias"
}

module "sops" {
  source = "../../modules/sops"

  env         = module.platform.env
  parent_env  = module.platform.parent_env
  kms_key_arn = module.platform.kms_key_arn
}

output "sopsw" {
  description = "Command to edit the current environment's encrypted values file"
  value       = module.sops.sopsw
}

output "ssm_parameters" {
  description = "SSM parameters provisioned from SOPS config"
  sensitive   = true
  value       = module.sops.ssm_parameters
}

output "parameter_count" {
  description = "Number of SSM parameters provisioned"
  value       = module.sops.parameter_count
}
