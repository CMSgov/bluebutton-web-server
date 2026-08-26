data "aws_ssm_parameter" "bcda_account_id" {
  name = "/bb/${local.env}/app/sensitive/bcda_account_id"
}

data "aws_secretsmanager_secret_version" "datadog_cicd_api_key" {
  secret_id = "arn:aws:secretsmanager:${var.region}:${sensitive(data.aws_ssm_parameter.bcda_account_id.value)}:secret:/cdap/bb/${local.env}/datadog/cicd/api-key"
}

data "aws_secretsmanager_secret_version" "datadog_cicd_application_key" {
  secret_id = "arn:aws:secretsmanager:${var.region}:${sensitive(data.aws_ssm_parameter.bcda_account_id.value)}:secret:/cdap/bb/${local.env}/datadog/cicd/application-key"
}

data "aws_ssm_parameter" "hostname_url" {
  name = "/${local.app}/${local.env}/app/nonsensitive/hostname_url"
}

data "aws_ssm_parameter" "bb_akamai_aca_token" {
  name = "/${local.app}/${local.env}/app/sensitive/bb_akamai_aca_token"
}

data "aws_ssm_parameter" "medicare_slsx_akamai_aca_token" {
  name = "/${local.app}/${local.env}/app/sensitive/medicare_slsx_akamai_aca_token"
}

data "aws_ssm_parameter" "medicare_gov_synthetic_tests_akamai_token" {
  name = "/${local.app}/${local.env}/app/sensitive/medicare_gov_synthetic_tests_akamai_token"
}

data "aws_ssm_parameter" "datadog_bbuser00000_access_token" {
  name = "/${local.app}/${local.env}/app/sensitive/datadog_bbuser00000_access_token"
}

data "aws_ssm_parameter" "datadog_bbuser10000_access_token" {
  name = "/${local.app}/${local.env}/app/sensitive/datadog_bbuser10000_access_token"
}
