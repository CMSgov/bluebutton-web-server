# CloudWatch Alarms for Blue Button Microservices

# SNS Topic for Alarm Notifications
resource "aws_sns_topic" "alarms" {
  name              = "bb-${local.workspace}-cloudwatch-alarms"
  kms_master_key_id = local.platform.kms_key_arn

  tags = merge(local.common_tags, {
    Name = "bb-${local.workspace}-cloudwatch-alarms"
  })
}

# Email Subscription (Optional)
resource "aws_sns_topic_subscription" "alarms_email" {
  count     = var.alarm_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alarms.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

# ============================================================================
# Infrastructure Alarms (Deadman Switch & ELB)
# ============================================================================

# Alarm: Log Availability (Deadman Switch) - BFD Pattern
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
  alarm_actions     = [aws_sns_topic.alarms.arn]
  ok_actions        = [aws_sns_topic.alarms.arn]

  dimensions = {
    LogGroupName = aws_cloudwatch_log_group.ecs[each.key].name
  }

  tags = merge(local.common_tags, {
    Name = "bb-${local.workspace}-${each.key}-log-availability"
  })
}

# Alarm: ELB 5xx Errors (Infrastructure/Routing) - AB2D Pattern
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
  alarm_actions     = [aws_sns_topic.alarms.arn]

  dimensions = {
    LoadBalancer = aws_lb.alb[each.key].arn_suffix
  }

  tags = merge(local.common_tags, {
    Name = "bb-${local.workspace}-${each.key}-elb-5xx-errors"
  })
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
  alarm_actions      = [aws_sns_topic.alarms.arn]
  ok_actions         = [aws_sns_topic.alarms.arn]

  dimensions = {
    LoadBalancer = aws_lb.alb[each.key].arn_suffix
    TargetGroup  = aws_lb_target_group.tg[each.key].arn_suffix
  }

  tags = merge(local.common_tags, {
    Name = "bb-${local.workspace}-${each.key}-no-healthy-hosts"
  })
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
  alarm_actions     = [aws_sns_topic.alarms.arn]

  dimensions = {
    LoadBalancer = aws_lb.alb[each.key].arn_suffix
    TargetGroup  = aws_lb_target_group.tg[each.key].arn_suffix
  }

  tags = merge(local.common_tags, {
    Name = "bb-${local.workspace}-${each.key}-api-5xx-errors"
  })
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
  threshold           = "5000" # 5 seconds in milliseconds

  alarm_description = "${each.key} API p99 latency above threshold"
  alarm_actions     = [aws_sns_topic.alarms.arn]

  dimensions = {
    LoadBalancer = aws_lb.alb[each.key].arn_suffix
    TargetGroup  = aws_lb_target_group.tg[each.key].arn_suffix
  }

  tags = merge(local.common_tags, {
    Name = "bb-${local.workspace}-${each.key}-api-latency-high"
  })
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
  alarm_actions     = [aws_sns_topic.alarms.arn]

  dimensions = {
    LoadBalancer = aws_lb.alb[each.key].arn_suffix
    TargetGroup  = aws_lb_target_group.tg[each.key].arn_suffix
  }

  tags = merge(local.common_tags, {
    Name = "bb-${local.workspace}-${each.key}-api-4xx-errors"
  })
}
