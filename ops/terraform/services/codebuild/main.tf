# CodeBuild Terraservice
# Run this independently from ECS infrastructure

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket               = "bb2-terraform-state"
    key                  = "codebuild/terraform.tfstate"
    region               = "us-east-1"
    encrypt              = true
    workspace_key_prefix = "codebuild"
  }
}

provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      application = "bluebutton"
      environment = local.env
      service     = "codebuild"
      managed_by  = "opentofu"
    }
  }
}

locals {
  env = terraform.workspace
}

# ECR Repository for storing built images
resource "aws_ecr_repository" "api" {
  name                 = "bb-${local.env}-api"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "api" {
  repository = aws_ecr_repository.api.name

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

# CodeBuild module
module "codebuild" {
  source = "../../modules/bb-codebuild"

  env                = local.env
  ecr_repository_arn = aws_ecr_repository.api.arn
  ecr_repository_url = aws_ecr_repository.api.repository_url
}

# Variables for GitHub Actions OIDC
variable "github_org" {
  type        = string
  description = "GitHub organization name"
  default     = "CMSgov"
}

variable "github_repo" {
  type        = string
  description = "GitHub repository name"
  default     = "bluebutton-web-server"
}

variable "iam_path" {
  type        = string
  description = "IAM path for roles and policies"
  default     = "/"
}

variable "permissions_boundary_arn" {
  type        = string
  description = "ARN of IAM permissions boundary (optional)"
  default     = null
}
