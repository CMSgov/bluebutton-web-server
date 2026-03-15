# ============================================================================
# Platform Module (CMS Cloud Terraservice Pattern)
# ============================================================================
module "platform" {
  source    = "../../modules/platform"
  providers = { aws = aws, aws.secondary = aws.secondary }

  app         = local.app
  env         = local.env
  service     = local.service
  root_module = "https://github.com/CMSgov/bluebutton-web-server/tree/main/ops/services/30-notifications"
}

# ============================================================================
# Locals
# ============================================================================
locals {
  env     = terraform.workspace
  service = "notifications"

  workspace    = module.platform.env
  app_prefix   = module.platform.app
  region       = module.platform.primary_region.id
  account_id   = module.platform.account_id
  default_tags = module.platform.default_tags

  # Services to configure notifications for (matches 20-microservices backend_services)
  notification_services = toset(var.backend_services)
}

# ============================================================================
# Data Sources — Discover SNS Topic ARNs from 20-microservices via SSM
# ============================================================================
data "aws_ssm_parameter" "sns_topic_arn" {
  for_each = local.notification_services
  name     = "/bb/${local.workspace}/notifications/config/sns_topic_arn_${each.key}"
}

# ============================================================================
# Splunk On-Call HTTPS Subscription
# Routes CloudWatch alarm notifications to Splunk On-Call REST API.
# Splunk On-Call delivers to Slack via its native integration.
# ============================================================================
resource "aws_sns_topic_subscription" "splunk_oncall_https" {
  for_each               = var.splunk_oncall_https_url != "" ? local.notification_services : toset([])
  topic_arn              = data.aws_ssm_parameter.sns_topic_arn[each.key].value
  protocol               = "https"
  endpoint               = var.splunk_oncall_https_url
  endpoint_auto_confirms = true
}

# ============================================================================
# Splunk On-Call Email Routing Subscription
# Alternative delivery path via Splunk On-Call's email integration.
# ============================================================================
resource "aws_sns_topic_subscription" "splunk_oncall_email" {
  for_each  = var.splunk_oncall_email != "" ? local.notification_services : toset([])
  topic_arn = data.aws_ssm_parameter.sns_topic_arn[each.key].value
  protocol  = "email"
  endpoint  = var.splunk_oncall_email
}
