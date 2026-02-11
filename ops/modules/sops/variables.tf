# ops/modules/sops/variables.tf
# Input variables — designed for BB2's platform module interface

variable "env" {
  description = "Current environment name (e.g., test, test-pr-123)"
  type        = string
}

variable "parent_env" {
  description = "Parent/established environment (test, sandbox, prod)"
  type        = string
}

variable "kms_key_arn" {
  description = "KMS key ARN for encrypting SecureString SSM parameters"
  type        = string
}

variable "values_dir" {
  description = "Path to the values directory containing .sopsw.yaml files. Defaults to {root}/values"
  type        = string
  default     = null
}

variable "values_file_extension" {
  description = "File extension for sopsw values files"
  type        = string
  default     = "sopsw.yaml"
}

variable "values_file" {
  description = "Override the values file name. Defaults to {parent_env}.{extension}"
  type        = string
  default     = null
}

variable "create_sopsw_wrapper" {
  description = "Create a local bin/sopsw script for editing encrypted files"
  type        = bool
  default     = true
}
