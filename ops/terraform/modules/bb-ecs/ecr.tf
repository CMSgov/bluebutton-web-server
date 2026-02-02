# terraform/modules/bb-ecs/repos.tf

resource "aws_ecr_repository" "repo" {
  for_each             = nonsensitive(local.service_config)
  name                 = "${local.app_prefix}-${local.workspace}-${each.key}-image"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = merge(local.common_tags, {
    Name = "${local.app_prefix}-${local.workspace}-${each.key}-image"
  })
}

# Lifecycle policy to clean up old images
resource "aws_ecr_lifecycle_policy" "repo" {
  for_each   = local.service_config
  repository = aws_ecr_repository.repo[each.key].name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 30 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 30
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}
