# AWS Providers Configuration

provider "aws" {
  region = var.region

  default_tags {
    tags = module.platform.default_tags
  }
}

provider "aws" {
  alias  = "secondary"
  region = var.secondary_region

  default_tags {
    tags = module.platform.default_tags
  }
}
