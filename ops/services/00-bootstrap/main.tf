# ============================================================================
# Platform Module (CMS Cloud Terraservice Pattern)
# ============================================================================
module "platform" {
  source    = "../../modules/platform"
  providers = { aws = aws, aws.secondary = aws.secondary }

  app         = "bb"
  env         = local.env
  root_module = "https://github.com/CMSgov/bluebutton-web-server/tree/main/ops/services/00-bootstrap"
  service     = local.service
}

locals {
  # Environment from workspace
  env = terraform.workspace

  # Map platform outputs to local variables
  vpc_id               = module.platform.vpc_id
  public_subnet_ids    = module.platform.public_subnet_ids
  private_subnet_ids   = module.platform.private_subnet_ids
  kms_key_arn          = module.platform.kms_key_arn
  secondary_region     = var.secondary_region
  permissions_boundary = module.platform.permissions_boundary

  # Standardize service name
  service = "bootstrap"

  # CodeBuild configuration
  project_name = "bb-${local.bucket_env}-web-server"
  repo_env     = local.env == "sandbox" ? "prod" : local.env

  # Conditional resource creation (sandbox doesn't create resources, reuses prod)
  create_resources = local.env != "sandbox"
}

# ============================================================================
# Environment KMS Key (pre-existing, managed externally)
# Uses existing key: alias/bb-{env}-app-key
# ============================================================================
data "aws_kms_alias" "env" {
  name = "alias/bb-${local.env}-app-key-alias"
}

# ============================================================================
# ECR Repositories (Global/Shared)
# ============================================================================
resource "aws_kms_key" "ecr" {
  count                   = local.create_resources ? 1 : 0
  description             = "bb-${local.bucket_env}-ecr"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = {
    Name = "bb-${local.bucket_env}-ecr"
  }
}

resource "aws_kms_alias" "ecr" {
  count         = local.create_resources ? 1 : 0
  name          = "alias/bb-${local.bucket_env}-ecr"
  target_key_id = aws_kms_key.ecr[0].key_id
}

resource "aws_ecr_repository" "api" {
  count                = local.create_resources ? 1 : 0
  name                 = "bb-${local.bucket_env}-api"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.ecr[0].arn
  }

  tags = {
    Name    = "bb-${local.bucket_env}-api"
    service = "api"
  }
}

resource "aws_ecr_lifecycle_policy" "api" {
  count      = local.create_resources ? 1 : 0
  repository = aws_ecr_repository.api[0].name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 30 images"
      selection = {
        tagStatus     = "tagged"
        tagPrefixList = ["v"]
        countType     = "imageCountMoreThan"
        countNumber   = 30
      }
      action = { type = "expire" }
    }]
  })
}
