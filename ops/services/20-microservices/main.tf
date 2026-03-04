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

      # ALB targets gunicorn (HTTPS on 8443 with DigiCert TLS)
      port = coalesce(
        try(local.ssm_service_configs[service_name].port, null),
        8443
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

  # Secrets to exclude from container injection
  # - Infrastructure/EC2 artifacts not needed by the Django app in Fargate
  # - slsx_verify_ssl_* are non-sensitive, handled via SSM nonsensitive path
  #   (SOPS → /bb/{env}/app/nonsensitive/django_slsx_verify_ssl_* → DJANGO_SLSX_VERIFY_SSL_*)
  secrets_exclude = toset([
    "ssh_users",
    "mon_nessus_pub_key",
    "mon_nessus_pwd",
    "mon_nessus_user",
    "tfbackend",
    "tfbackend2",
    "cf_app_pyapps_pwd",
    "slsx_verify_ssl_internal",
    "slsx_verify_ssl_external",
  ])

  # SM basenames that need renaming to match Django env var names
  # Auto-discovery uppercases basename: /bb2/{env}/app/slsx_client_id → SLSX_CLIENT_ID
  # But Django expects DJANGO_SLSX_CLIENT_ID (legacy env.j2 added the DJANGO_ prefix)
  secret_name_overrides = {
    "SLSX_CLIENT_ID"                 = "DJANGO_SLSX_CLIENT_ID"
    "SLSX_CLIENT_SECRET"             = "DJANGO_SLSX_CLIENT_SECRET"
    "MEDICARE_SLSX_AKAMAI_ACA_TOKEN" = "DJANGO_MEDICARE_SLSX_AKAMAI_ACA_TOKEN"
    "MEDICARE_SLSX_LOGIN_URI"        = "DJANGO_MEDICARE_SLSX_LOGIN_URI"
    "MEDICARE_SLSX_REDIRECT_URI"     = "DJANGO_MEDICARE_SLSX_REDIRECT_URI"
    "SLSX_HEALTH_CHECK_ENDPOINT"     = "DJANGO_SLSX_HEALTH_CHECK_ENDPOINT"
    "SLSX_TOKEN_ENDPOINT"            = "DJANGO_SLSX_TOKEN_ENDPOINT"
    "SLSX_SIGNOUT_ENDPOINT"          = "DJANGO_SLSX_SIGNOUT_ENDPOINT"
    "SLSX_USERINFO_ENDPOINT"         = "DJANGO_SLSX_USERINFO_ENDPOINT"
    "DJANGO_ADMIN_REDIRECTOR"        = "DJANGO_ADMIN_PREPEND_URL"
  }

  # Transform Secrets Manager secrets to ECS format, filtering out infrastructure-only secrets
  # Path /bb2/{env}/app/slsx_client_id → SLSX_CLIENT_ID → lookup → DJANGO_SLSX_CLIENT_ID
  secrets_manager_discovered = [
    for secret in data.aws_secretsmanager_secret.app_secrets : {
      name = lookup(
        local.secret_name_overrides,
        replace(upper(replace(basename(secret.name), "-", "_")), "/[^A-Z0-9_]/", "_"),
        replace(upper(replace(basename(secret.name), "-", "_")), "/[^A-Z0-9_]/", "_")
      )
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

  # Default environment variables — infrastructure/runtime config only
  # Django app config (HOSTNAME_URL, email, S3, etc.) comes from SSM via SOPS seed
  # TARGET_ENV comes from SSM nonsensitive (SOPS seed), no need to duplicate here
  default_environment = [
    { name = "ENVIRONMENT", value = local.workspace },
    { name = "DJANGO_FHIR_CERTSTORE", value = "/tmp/certstore" },
    { name = "FHIR_CERT_FILE", value = "ca.cert.pem" },
    { name = "FHIR_KEY_FILE", value = "ca.key.nocrypt.pem" },
    { name = "PYTHONUNBUFFERED", value = "1" },
    { name = "PYTHONDONTWRITEBYTECODE", value = "1" },
    # NewRelic APM configuration (NEW_RELIC_APP_NAME comes from SSM seed)
    { name = "NEW_RELIC_MONITOR_MODE", value = "true" },
    { name = "NEW_RELIC_LOG", value = "stdout" },
    { name = "NEW_RELIC_LOG_LEVEL", value = "info" },
    { name = "NEW_RELIC_DISTRIBUTED_TRACING_ENABLED", value = "true" },
  ]

  # SSM individual params → ECS environment format
  # basename(/bb/test/app/nonsensitive/debug) → DEBUG
  # basename(/bb/test/app/nonsensitive/django_from_email) → DJANGO_FROM_EMAIL
  ssm_environment = [
    for i, name in data.aws_ssm_parameters_by_path.app_nonsensitive.names : {
      name  = upper(replace(basename(name), "-", "_"))
      value = nonsensitive(data.aws_ssm_parameters_by_path.app_nonsensitive.values[i])
    }
  ]

  # Merge: hardcoded defaults + SSM-discovered nonsensitive + user overrides
  # Later entries win on duplicate keys (ECS behavior)
  all_environment = concat(
    local.default_environment,
    local.ssm_environment,
    var.environment_variables
  )
}

