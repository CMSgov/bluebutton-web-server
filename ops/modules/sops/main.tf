# ops/modules/sops/main.tf
# Local SOPS module for BB2 — decrypts sopsw files and provisions SSM parameters

locals {
  # File paths
  values_dir       = coalesce(var.values_dir, "${path.root}/values")
  values_file      = coalesce(var.values_file, "${var.parent_env}.${var.values_file_extension}")
  values_file_path = "${local.values_dir}/${local.values_file}"

  # Template variable regex — matches ${env} and %env patterns in SSM keys/values
  template_var_regex = "/\\$\\{{0,1}%s\\}{0,1}/"

  # Read and parse the encrypted sopsw YAML
  raw_sopsw_yaml     = file(local.values_file_path)
  enc_data           = yamldecode(local.raw_sopsw_yaml)
  nonsensitive_regex = local.enc_data.sops.unencrypted_regex

  # Decrypted data from sopsw
  decrypted_data = yamldecode(data.external.decrypted_sops.result.decrypted_sops)

  # Build SSM config from decrypted values
  ssm_config = {
    for key, val in nonsensitive(local.decrypted_data) : key => {
      str_val      = tostring(val)
      is_sensitive = length(regexall(local.nonsensitive_regex, key)) == 0
      source       = basename(local.values_file)
    } if lower(tostring(val)) != "undefined"
  }

  # Replace ${env} template variables with actual environment name
  env_config = {
    for k, v in local.ssm_config
    : replace(k, format(local.template_var_regex, "env"), var.env) => {
      str_val      = replace(v.str_val, format(local.template_var_regex, "env"), var.env)
      is_sensitive = v.is_sensitive
      source       = v.source
    }
  }
}

# Decrypt sopsw file using the wrapper script
# sopsw handles: ${ACCOUNT_ID} substitution, lastmodified/mac injection, then sops decrypt
data "external" "decrypted_sops" {
  program = [
    "bash",
    "-c",
    <<-EOF
    ${path.module}/bin/sopsw -d ${local.values_file_path} | yq -o=json '{"decrypted_sops": (. | tostring)}'
    EOF
  ]
}

# Provision SSM parameters from decrypted config
resource "aws_ssm_parameter" "this" {
  for_each = local.env_config

  name           = each.key
  tier           = "Intelligent-Tiering"
  value          = each.value.is_sensitive ? each.value.str_val : null
  insecure_value = each.value.is_sensitive ? null : try(nonsensitive(each.value.str_val), each.value.str_val)
  type           = each.value.is_sensitive ? "SecureString" : "String"
  key_id         = each.value.is_sensitive ? var.kms_key_arn : null

  tags = {
    source_file    = each.value.source
    managed_config = true
  }
}

# Create local sopsw wrapper for editing encrypted files
resource "local_file" "sopsw" {
  count    = var.create_sopsw_wrapper ? 1 : 0
  content  = file("${path.module}/bin/sopsw")
  filename = "${path.root}/bin/sopsw"
}
