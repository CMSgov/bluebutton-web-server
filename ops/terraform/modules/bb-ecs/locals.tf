# terraform/modules/bb-ecs/locals.tf
# All configuration loaded from SSM Parameter Store - NO DEFAULTS

locals {
  # Get values from platform object
  workspace       = var.platform.env
  app_prefix      = var.platform.app
  cluster_name    = var.create_cluster ? "${local.app_prefix}-${local.workspace}" : var.cluster_name
  private_subnets = var.platform.private_subnet_ids
  public_subnets  = var.platform.public_subnet_ids
  region          = var.platform.primary_region.name
  account_id      = var.platform.account_id

  # SSM path prefix
  ssm_config_path = "/bluebutton/config"
  ssm_common_path = "/bluebutton/common"

  # Build service configuration from SSM - ALL VALUES REQUIRED
  service_config = {
    for k, v in var.backend_services : k => {
      name              = k
      port              = tonumber(local.ssm_config["${local.ssm_config_path}/${k}_port"])
      cpu               = tonumber(local.ssm_config["${local.ssm_config_path}/${k}_cpu"])
      memory            = tonumber(local.ssm_config["${local.ssm_config_path}/${k}_memory"])
      count             = tonumber(local.ssm_config["${local.ssm_config_path}/${k}_count"])
      min_capacity      = tonumber(local.ssm_config["${local.ssm_config_path}/${k}_min_capacity"])
      max_capacity      = tonumber(local.ssm_config["${local.ssm_config_path}/${k}_max_capacity"])
      health_check_path = local.ssm_config["${local.ssm_config_path}/${k}_health_check_path"]
      alb               = tobool(local.ssm_config["${local.ssm_config_path}/${k}_alb"])
      autoscale_enabled = tobool(local.ssm_config["${local.ssm_config_path}/${k}_autoscale_enabled"])
    }
  }

  # VPC ID from SSM
  vpc_id = local.ssm_config["${local.ssm_common_path}/vpc_id"]

  # AZs from SSM (stored as JSON array)
  azs = jsondecode(local.ssm_config["${local.ssm_common_path}/azs"])

  common_tags = var.platform.default_tags

  # Certificate secrets auto-built from ARN variables
  # These are merged with var.secrets when passed to container template
  certificate_secrets = compact([
    var.www_key_secret_arn != "" ? jsonencode({ name = "WWW_KEY_FILE_B64", valueFrom = var.www_key_secret_arn }) : "",
    var.www_cert_secret_arn != "" ? jsonencode({ name = "WWW_COMBINED_CRT_B64", valueFrom = var.www_cert_secret_arn }) : "",
    var.fhir_cert_secret_arn != "" ? jsonencode({ name = "FHIR_CERT_PEM_B64", valueFrom = var.fhir_cert_secret_arn }) : "",
    var.fhir_key_secret_arn != "" ? jsonencode({ name = "FHIR_KEY_PEM_B64", valueFrom = var.fhir_key_secret_arn }) : ""
  ])

  # Merge user-provided secrets with certificate secrets
  all_secrets = concat(
    var.secrets,
    [for s in local.certificate_secrets : jsondecode(s)]
  )

  # Default environment variables (migrated from env.j2 template)
  # These are the core Django settings needed for the application
  default_environment = [
    { name = "TARGET_ENV", value = local.workspace },
    { name = "ENVIRONMENT", value = local.workspace },
    { name = "PORT", value = "8000" },
    { name = "DJANGO_FHIR_CERTSTORE", value = "/app/certstore" },
    { name = "FHIR_CERT_FILE", value = "ca.cert.pem" },
    { name = "FHIR_KEY_FILE", value = "ca.key.nocrypt.pem" },
    { name = "PYTHONUNBUFFERED", value = "1" },
    { name = "PYTHONDONTWRITEBYTECODE", value = "1" },
  ]

  # Merge default env vars with user-provided env vars
  all_environment = concat(
    local.default_environment,
    var.environment_variables
  )
}
