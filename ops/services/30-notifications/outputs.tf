# terraform/services/30-notifications/outputs.tf

output "sns_topic_arns" {
  description = "SNS alarm topic ARNs discovered from 20-microservices"
  value       = { for k, v in data.aws_ssm_parameter.sns_topic_arn : k => v.value }
  sensitive   = true
}

output "splunk_oncall_https_subscriptions" {
  description = "Splunk On-Call HTTPS subscription ARNs"
  value       = { for k, v in aws_sns_topic_subscription.splunk_oncall_https : k => v.arn }
  sensitive   = true
}
