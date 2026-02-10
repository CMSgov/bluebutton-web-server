# ============================================================================
# Platform Module (CMS Cloud Terraservice Pattern)
# Provides: SSM config, VPC, subnets, KMS, ACM, environment detection
# ============================================================================
module "platform" {
  source    = "../../modules/platform"
  providers = { aws = aws, aws.secondary = aws.secondary }

  app                          = local.app
  env                          = local.env
  service                      = local.service
  root_module                  = "https://github.com/CMSgov/bluebutton-web-server/tree/main/ops/services/20-microservices"
  kms_key_alias                = "alias/bb-${local.env}-app-key-alias"
  enable_acm_lookup            = true
  enable_security_group_lookup = true
}

# ============================================================================
# Locals
# ============================================================================

locals {
  # Required by root.tofu.tf (symlinked)
  env     = terraform.workspace
  service = "microservices"

  # Platform shortcuts (BFD pattern: flat locals from module outputs)
  workspace            = module.platform.env
  app_prefix           = module.platform.app
  cluster_name         = data.aws_ecs_cluster.main.cluster_name
  private_subnets      = module.platform.private_subnet_ids
  public_subnets       = module.platform.public_subnet_ids
  region               = module.platform.primary_region.id
  account_id           = module.platform.account_id
  vpc_id               = module.platform.vpc_id
  azs                  = [for s in values(module.platform.private_subnets) : s.availability_zone]
  default_tags         = module.platform.default_tags
  kms_key_arn          = module.platform.kms_key_arn
  kms_alias            = module.platform.kms_alias
  acm_certificate      = module.platform.acm_certificate
  permissions_boundary = module.platform.permissions_boundary

  # Terraservice-style SSM root mapping
  ssm_root_map = {
    microservices = "/bb/${local.env}/microservices/"
    common        = "/bb/${local.env}/common/"
    config        = "/bb/${local.env}/config/"
    core          = "/bb/${local.env}/core/"
  }

  # ============================================================================
  # Service Configuration (SSM JSON + overrides)
  # Priority: var.service_overrides > SSM JSON (/bb/{env}/{service}/config) > defaults
  # ============================================================================

  service_config = {
    for service_name in var.backend_services : service_name => {
      name = service_name

      port = coalesce(
        try(local.ssm_service_configs[service_name].port, null),
        8000
      )

      cpu = coalesce(
        try(var.service_overrides[service_name].cpu, null),
        try(local.ssm_service_configs[service_name].cpu, null),
        512
      )

      memory = coalesce(
        try(var.service_overrides[service_name].memory, null),
        try(local.ssm_service_configs[service_name].memory, null),
        1024
      )

      count = coalesce(
        try(var.service_overrides[service_name].count, null),
        try(local.ssm_service_configs[service_name].count, null),
        1
      )

      min_capacity = coalesce(
        try(var.service_overrides[service_name].min_capacity, null),
        try(local.ssm_service_configs[service_name].scaling_min, null),
        1
      )

      max_capacity = coalesce(
        try(var.service_overrides[service_name].max_capacity, null),
        try(local.ssm_service_configs[service_name].scaling_max, null),
        2
      )

      health_check_path = coalesce(
        try(var.service_overrides[service_name].health_check_path, null),
        try(local.ssm_service_configs[service_name].health_check_path, null),
        "/health"
      )

      alb = try(
        local.ssm_service_configs[service_name].alb_enabled,
        true
      )

      autoscale_enabled = try(
        local.ssm_service_configs[service_name].autoscale_enabled,
        false
      )
    }
  }

  # ============================================================================
  # Dynamic Secret Discovery - Secrets Manager only
  # ============================================================================

  # Infrastructure-only secrets to exclude from container injection
  # These are EC2/Ansible artifacts not needed by the Django app in Fargate
  secrets_exclude = toset([
    "ssh_users",
    "mon_nessus_pub_key",
    "mon_nessus_pwd",
    "mon_nessus_user",
    "tfbackend",
    "tfbackend2",
    "www_combined_crt",
    "www_key_file",
    "cf_app_pyapps_pwd",
  ])

  # Transform Secrets Manager secrets to ECS format, filtering out infrastructure-only secrets
  # Path /bb2/{env}/app/secret_key → ENV var SECRET_KEY
  secrets_manager_discovered = [
    for secret in data.aws_secretsmanager_secret.app_secrets : {
      name      = replace(upper(replace(basename(secret.name), "-", "_")), "/[^A-Z0-9_]/", "_")
      valueFrom = secret.arn
    }
    if !contains(local.secrets_exclude, basename(secret.name))
  ]

  # All secrets: auto-discovered from Secrets Manager /bb2/{env}/app/* + explicit overrides
  all_secrets = concat(
    local.secrets_manager_discovered,
    var.secrets
  )

  # ============================================================================
  # Environment Variables
  # ============================================================================

  # Default environment variables (migrated from env.j2 template)
  default_environment = [
    { name = "TARGET_ENV", value = local.workspace },
    { name = "ENVIRONMENT", value = local.workspace },
    { name = "PORT", value = "8000" },
    { name = "DJANGO_FHIR_CERTSTORE", value = "/app/certstore" },
    { name = "FHIR_CERT_FILE", value = "ca.cert.pem" },
    { name = "FHIR_KEY_FILE", value = "ca.key.nocrypt.pem" },
    { name = "PYTHONUNBUFFERED", value = "1" },
    { name = "PYTHONDONTWRITEBYTECODE", value = "1" },
    # NewRelic APM configuration
    { name = "NEW_RELIC_APP_NAME", value = "BlueButton-${local.workspace}" },
    { name = "NEW_RELIC_MONITOR_MODE", value = "true" },
    { name = "NEW_RELIC_LOG", value = "stdout" },
    { name = "NEW_RELIC_LOG_LEVEL", value = "info" },
    { name = "NEW_RELIC_DISTRIBUTED_TRACING_ENABLED", value = "true" },
  ]

  # Merge default env vars with user-provided env vars
  all_environment = concat(
    local.default_environment,
    var.environment_variables
  )
}

