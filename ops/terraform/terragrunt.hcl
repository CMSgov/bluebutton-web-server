locals {
  # Determine the current environment based on the path.
  # This assumes your project structure has environment folders directly under the root,
  # like:
  # project-root/
  # ├── terragrunt.hcl
  # ├── test/
  # │   └── terragrunt.hcl
  # ├── stage/
  # │   └── terragrunt.hcl
  # └── prod/
  #     └── terragrunt.hcl
  #
  # If you run terragrunt from 'test/', path_relative_to_include() will be "test".
  # If you run terragrunt from 'stage/', it will be "stage", and so on.
  current_environment = split("/", path_relative_to_include())[0]

  # Determine the backend bucket name based on the current_environment.
  # If 'current_environment' is "test", use 'bb2-terraform-state'.
  # Otherwise, use 'bb-prd-app-config'.
  backend_bucket = can(regex("^(test|test_canary)$", local.current_environment)) ? "bb2-terraform-state" : "bb-prd-app-config"
}

remote_state {
  backend = "s3"
  generate = {
    path        = "backend.tf"
    if_exists   = "overwrite_terragrunt"
  }
  config = {
    bucket         = local.backend_bucket
    key            = "${path_relative_to_include()}/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    use_lockfile   = "true"
    #dynamodb_table = "bb-terraform-state" # This remains constant for all environments
  }
}