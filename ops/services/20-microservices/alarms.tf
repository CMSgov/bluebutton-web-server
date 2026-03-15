# CloudWatch Alarms for Blue Button Microservices

# SNS Topic for Alarm Notifications (per-service)
resource "aws_sns_topic" "alarms" {
  for_each          = nonsensitive(local.service_config)
  name              = "bb-${local.workspace}-${each.key}-cloudwatch-alarms"
  kms_master_key_id = local.kms_key_arn

  tags = {
    Name = "bb-${local.workspace}-${each.key}-cloudwatch-alarms"
  }
}

# Email Subscription (Optional, per-service)
resource "aws_sns_topic_subscription" "alarms_email" {
  for_each  = var.alarm_email != "" ? nonsensitive(local.service_config) : {}
  topic_arn = aws_sns_topic.alarms[each.key].arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

# ============================================================================
# GuardDuty Runtime Monitoring
# ============================================================================

# EventBridge rule to detect when GuardDuty runtime agent stops sending telemetry.
# Disabled by default until alerts are tuned (ref: BFD-4379 in upstream BFD project).
resource "aws_cloudwatch_event_rule" "guardduty_runtime_health" {
  name        = "bb-${local.workspace}-guardduty-runtime-health"
  state       = "DISABLED"
  description = "Capture events indicating a GuardDuty runtime agent is no longer sending telemetry"

  event_pattern = jsonencode({
    source      = ["aws.guardduty"]
    detail-type = ["GuardDuty Runtime Protection Unhealthy"]
  })

  tags = {
    Name = "bb-${local.workspace}-guardduty-runtime-health"
  }
}

resource "aws_cloudwatch_event_target" "guardduty_runtime_health" {
  for_each = nonsensitive(local.service_config)

  rule      = aws_cloudwatch_event_rule.guardduty_runtime_health.name
  target_id = "guardduty-health-${each.key}"
  arn       = aws_sns_topic.alarms[each.key].arn
}

# EventBridge rule for GuardDuty security findings (MEDIUM severity and above)
resource "aws_cloudwatch_event_rule" "guardduty_findings" {
  name        = "bb-${local.workspace}-guardduty-findings"
  description = "Capture GuardDuty findings with MEDIUM severity or higher"

  event_pattern = jsonencode({
    source      = ["aws.guardduty"]
    detail-type = ["GuardDuty Finding"]
    detail = {
      severity = [{ numeric = [">=", 4] }]
    }
  })

  tags = {
    Name = "bb-${local.workspace}-guardduty-findings"
  }
}

resource "aws_cloudwatch_event_target" "guardduty_findings" {
  for_each = nonsensitive(local.service_config)

  rule      = aws_cloudwatch_event_rule.guardduty_findings.name
  target_id = "guardduty-findings-${each.key}"
  arn       = aws_sns_topic.alarms[each.key].arn
}

# ============================================================================
# SSM Export: SNS Topic ARN for cross-service discovery
# Consumed by 30-notifications for Splunk On-Call / Slack routing
# ============================================================================
resource "aws_ssm_parameter" "sns_topic_arn" {
  for_each = nonsensitive(local.service_config)
  name     = "/bb/${local.workspace}/notifications/config/sns_topic_arn_${each.key}"
  type     = "String"
  value    = aws_sns_topic.alarms[each.key].arn

  tags = {
    Name = "bb-${local.workspace}-${each.key}-sns-topic-arn"
  }
}

# ============================================================================
# Infrastructure Alarms (Deadman Switch & ELB)
# ============================================================================

# Alarm: Log Availability (Deadman Switch)
# Triggers if no logs are received for 1 hour, indicating a silent failure
resource "aws_cloudwatch_metric_alarm" "log_availability" {
  for_each            = nonsensitive(local.service_config)
  alarm_name          = "bb-${local.workspace}-${each.key}-log-availability"
  comparison_operator = "LessThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "IncomingLogEvents"
  namespace           = "AWS/Logs"
  period              = "3600" # 1 hour
  statistic           = "Sum"
  threshold           = "0"
  treat_missing_data  = "breaching"

  alarm_description = "${each.key} logs have stopped flowing. Service may be deadlocked or sidecar failed."
  alarm_actions     = [aws_sns_topic.alarms[each.key].arn]
  ok_actions        = [aws_sns_topic.alarms[each.key].arn]

  dimensions = {
    LogGroupName = aws_cloudwatch_log_group.ecs[each.key].name
  }

  tags = {
    Name = "bb-${local.workspace}-${each.key}-log-availability"
  }
}

# Alarm: ELB 5xx Errors (Infrastructure/Routing)
# Catches errors where the LB fails to route to targets (e.g., no healthy hosts)
resource "aws_cloudwatch_metric_alarm" "elb_5xx_errors" {
  for_each            = nonsensitive({ for k, v in local.service_config : k => v if v.alb })
  alarm_name          = "bb-${local.workspace}-${each.key}-elb-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "HTTPCode_ELB_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = "60"
  statistic           = "Sum"
  threshold           = "10"
  treat_missing_data  = "notBreaching"

  alarm_description = "${each.key} Load Balancer returning 5xx errors (infrastructure/routing failure)"
  alarm_actions     = [aws_sns_topic.alarms[each.key].arn]

  dimensions = {
    LoadBalancer = aws_lb.alb[each.key].arn_suffix
  }

  tags = {
    Name = "bb-${local.workspace}-${each.key}-elb-5xx-errors"
  }
}

# ============================================================================
# Application Alarms (Target Group)
# ============================================================================

# Alarm: No Healthy Hosts
resource "aws_cloudwatch_metric_alarm" "unhealthy_hosts" {
  for_each            = nonsensitive({ for k, v in local.service_config : k => v if v.alb })
  alarm_name          = "bb-${local.workspace}-${each.key}-no-healthy-hosts"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "HealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = "60"
  statistic           = "Minimum"
  threshold           = "1"

  alarm_description  = "No healthy ECS tasks available for ${each.key} service"
  treat_missing_data = "breaching"
  alarm_actions      = [aws_sns_topic.alarms[each.key].arn]
  ok_actions         = [aws_sns_topic.alarms[each.key].arn]

  dimensions = {
    LoadBalancer = aws_lb.alb[each.key].arn_suffix
    TargetGroup  = aws_lb_target_group.tg[each.key].arn_suffix
  }

  tags = {
    Name = "bb-${local.workspace}-${each.key}-no-healthy-hosts"
  }
}

# Alarm: High Target 5xx Error Rate (Application Errors)
resource "aws_cloudwatch_metric_alarm" "api_5xx_errors" {
  for_each            = nonsensitive({ for k, v in local.service_config : k => v if v.alb })
  alarm_name          = "bb-${local.workspace}-${each.key}-api-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"

  alarm_description = "${each.key} API returning 5xx errors"
  alarm_actions     = [aws_sns_topic.alarms[each.key].arn]

  dimensions = {
    LoadBalancer = aws_lb.alb[each.key].arn_suffix
    TargetGroup  = aws_lb_target_group.tg[each.key].arn_suffix
  }

  tags = {
    Name = "bb-${local.workspace}-${each.key}-api-5xx-errors"
  }
}

# Alarm: High API Latency (P99)
resource "aws_cloudwatch_metric_alarm" "api_latency_p99" {
  for_each            = nonsensitive({ for k, v in local.service_config : k => v if v.alb })
  alarm_name          = "bb-${local.workspace}-${each.key}-api-latency-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  extended_statistic  = "p99"
  threshold           = "5" # TargetResponseTime unit is seconds

  alarm_description = "${each.key} API p99 latency above threshold"
  alarm_actions     = [aws_sns_topic.alarms[each.key].arn]

  dimensions = {
    LoadBalancer = aws_lb.alb[each.key].arn_suffix
    TargetGroup  = aws_lb_target_group.tg[each.key].arn_suffix
  }

  tags = {
    Name = "bb-${local.workspace}-${each.key}-api-latency-high"
  }
}

# Alarm: 4xx Error Rate (Client Errors)
resource "aws_cloudwatch_metric_alarm" "api_4xx_errors" {
  for_each            = nonsensitive({ for k, v in local.service_config : k => v if v.alb })
  alarm_name          = "bb-${local.workspace}-${each.key}-api-4xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HTTPCode_Target_4XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "100" # Higher threshold for client errors

  alarm_description = "${each.key} API high rate of 4xx client errors"
  alarm_actions     = [aws_sns_topic.alarms[each.key].arn]

  dimensions = {
    LoadBalancer = aws_lb.alb[each.key].arn_suffix
    TargetGroup  = aws_lb_target_group.tg[each.key].arn_suffix
  }

  tags = {
    Name = "bb-${local.workspace}-${each.key}-api-4xx-errors"
  }
}
