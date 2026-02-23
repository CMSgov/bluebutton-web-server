# GitHub Actions OIDC Authentication
# Allows GitHub Actions to assume an AWS IAM role via OIDC

# OIDC Provider for GitHub Actions
# Created once per AWS account (not per environment)
# Sandbox reuses the provider created by prod (same account)
resource "aws_iam_openid_connect_provider" "github_actions" {
  count = local.create_resources ? 1 : 0 # Only create in test and prod, not sandbox

  client_id_list = ["sts.amazonaws.com"]
  url            = "https://token.actions.githubusercontent.com"

  # GitHub's OIDC thumbprint (standard, rarely changes)
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

# Discover OIDC provider (works for all workspaces including sandbox)
data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  depends_on = [aws_iam_openid_connect_provider.github_actions]
}

# Trust policy: Allow GitHub Actions from this repo to assume the role
data "aws_iam_policy_document" "github_actions_assume_role" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [data.aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_org}/${var.github_repo}:*"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

# IAM Role for GitHub Actions (created per environment)
resource "aws_iam_role" "github_actions" {
  name                 = "bb-${local.env}-github-actions"
  path                 = var.iam_path
  permissions_boundary = local.permissions_boundary
  description          = "OIDC Assumable GitHub Actions Role for Blue Button"

  assume_role_policy    = data.aws_iam_policy_document.github_actions_assume_role.json
  force_detach_policies = true

  tags = {
    Name = "bb-${local.env}-github-actions"
  }
}

# ============================================================================
# Discover shared resources (ECR & CodeBuild) by name
# For prod/test: finds the resource we just created
# For sandbox: finds prod's resources (same account, bucket_env maps sandbox→prod)
# ============================================================================

data "aws_ecr_repository" "shared" {
  name = "bb-${local.bucket_env}-api"

  depends_on = [aws_ecr_repository.api]
}

# ============================================================================
# ECR permissions for GitHub Actions (push/pull images)
# All environments get this policy — sandbox references prod's ECR
# ============================================================================

data "aws_iam_policy_document" "github_actions_ecr" {
  statement {
    sid       = "AllowECRAuthorization"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    sid = "AllowECRImageOperations"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:PutImage",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload"
    ]
    resources = [data.aws_ecr_repository.shared.arn]
  }
}

resource "aws_iam_role_policy" "github_actions_ecr" {
  name   = "ecr"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.github_actions_ecr.json
}

# ============================================================================
# CodeBuild trigger permissions (to trigger builds from GHA)
# Only for environments that have a CodeBuild project (test, prod — not sandbox)
# ============================================================================

data "aws_iam_policy_document" "github_actions_codebuild" {
  count = local.create_resources ? 1 : 0

  statement {
    sid = "AllowCodeBuildTrigger"
    actions = [
      "codebuild:StartBuild",
      "codebuild:BatchGetBuilds"
    ]
    resources = [aws_codebuild_project.main[0].arn]
  }
}

resource "aws_iam_role_policy" "github_actions_codebuild" {
  count  = local.create_resources ? 1 : 0
  name   = "codebuild"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.github_actions_codebuild[0].json
}

# ============================================================================
# ECS deployment permissions (update services after image push)
# Scoped to this environment's cluster, services, and task definitions only
# ============================================================================

data "aws_iam_policy_document" "github_actions_ecs_deploy" {
  statement {
    sid = "AllowECSServiceDeploy"
    actions = [
      "ecs:UpdateService",
      "ecs:DescribeServices",
      "ecs:DescribeTasks",
      "ecs:ListTasks"
    ]
    resources = [
      "arn:aws:ecs:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:service/${local.app}-${local.env}-cluster/*",
      "arn:aws:ecs:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:task/${local.app}-${local.env}-cluster/*"
    ]
  }

  statement {
    sid = "AllowECSTaskDefinition"
    actions = [
      "ecs:RegisterTaskDefinition",
      "ecs:DescribeTaskDefinition",
      "ecs:ListTaskDefinitions",
      "ecs:DeregisterTaskDefinition"
    ]
    resources = ["*"]
  }

  statement {
    sid = "AllowECSDescribeCluster"
    actions = [
      "ecs:DescribeClusters"
    ]
    resources = [
      "arn:aws:ecs:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:cluster/${local.app}-${local.env}-cluster"
    ]
  }

  statement {
    sid     = "AllowPassRole"
    actions = ["iam:PassRole"]
    resources = [
      "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role${var.iam_path}${local.app}-${local.env}-*-task",
      "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role${var.iam_path}${local.app}-${local.env}-*-execution"
    ]
    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy" "github_actions_ecs_deploy" {
  name   = "ecs-deploy"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.github_actions_ecs_deploy.json
}

# ============================================================================
# OpenTofu CI/CD permissions (plan & apply via GitHub Actions)
# Follows AB2D pattern: explicit actions, resources = ["*"]
# Covers all 4 services: 00-bootstrap, 01-config, 10-cluster, 20-microservices
# ============================================================================

data "aws_iam_policy_document" "github_actions_tofu" {
  # ACM
  statement {
    sid = "ACM"
    actions = [
      "acm:DescribeCertificate",
      "acm:ListCertificates",
      "acm:ListTagsForCertificate",
    ]
    resources = ["*"]
  }

  # Application Auto Scaling
  statement {
    sid = "AutoScaling"
    actions = [
      "application-autoscaling:Describe*",
      "application-autoscaling:RegisterScalableTarget",
      "application-autoscaling:DeregisterScalableTarget",
      "application-autoscaling:PutScalingPolicy",
      "application-autoscaling:DeleteScalingPolicy",
    ]
    resources = ["*"]
  }

  # CloudWatch
  statement {
    sid = "CloudWatch"
    actions = [
      "cloudwatch:DescribeAlarms",
      "cloudwatch:DeleteAlarms",
      "cloudwatch:ListTagsForResource",
      "cloudwatch:PutMetricAlarm",
      "cloudwatch:TagResource",
      "cloudwatch:UntagResource",
    ]
    resources = ["*"]
  }

  # CloudWatch Logs
  statement {
    sid = "CloudWatchLogs"
    actions = [
      "logs:CreateLogGroup",
      "logs:DeleteLogGroup",
      "logs:DescribeLogGroups",
      "logs:ListTagsForResource",
      "logs:PutRetentionPolicy",
      "logs:TagResource",
      "logs:UntagResource",
    ]
    resources = ["*"]
  }

  # EC2
  statement {
    sid = "EC2"
    actions = [
      "ec2:AuthorizeSecurityGroupEgress",
      "ec2:AuthorizeSecurityGroupIngress",
      "ec2:CreateSecurityGroup",
      "ec2:CreateTags",
      "ec2:DeleteSecurityGroup",
      "ec2:DeleteTags",
      "ec2:Describe*",
      "ec2:RevokeSecurityGroupEgress",
      "ec2:RevokeSecurityGroupIngress",
    ]
    resources = ["*"]
  }

  # ECS
  statement {
    sid = "ECS"
    actions = [
      "ecs:CreateCluster",
      "ecs:CreateService",
      "ecs:DeleteCluster",
      "ecs:DeleteService",
      "ecs:DeregisterTaskDefinition",
      "ecs:Describe*",
      "ecs:List*",
      "ecs:PutClusterCapacityProviders",
      "ecs:RegisterTaskDefinition",
      "ecs:TagResource",
      "ecs:UntagResource",
      "ecs:UpdateCluster",
      "ecs:UpdateService",
    ]
    resources = ["*"]
  }

  # ELB
  statement {
    sid = "ELB"
    actions = [
      "elasticloadbalancing:AddTags",
      "elasticloadbalancing:CreateListener",
      "elasticloadbalancing:CreateLoadBalancer",
      "elasticloadbalancing:CreateRule",
      "elasticloadbalancing:CreateTargetGroup",
      "elasticloadbalancing:DeleteListener",
      "elasticloadbalancing:DeleteLoadBalancer",
      "elasticloadbalancing:DeleteRule",
      "elasticloadbalancing:DeleteTargetGroup",
      "elasticloadbalancing:Describe*",
      "elasticloadbalancing:ModifyListener",
      "elasticloadbalancing:ModifyLoadBalancerAttributes",
      "elasticloadbalancing:ModifyTargetGroupAttributes",
      "elasticloadbalancing:RemoveTags",
      "elasticloadbalancing:SetSecurityGroups",
      "elasticloadbalancing:SetSubnets",
    ]
    resources = ["*"]
  }

  # IAM
  statement {
    sid = "IAM"
    actions = [
      "iam:AttachRolePolicy",
      "iam:CreatePolicy",
      "iam:CreatePolicyVersion",
      "iam:CreateRole",
      "iam:DeletePolicy",
      "iam:DeletePolicyVersion",
      "iam:DeleteRole",
      "iam:DeleteRolePolicy",
      "iam:DetachRolePolicy",
      "iam:GetPolicy",
      "iam:GetPolicyVersion",
      "iam:GetRole",
      "iam:GetRolePolicy",
      "iam:ListAccountAliases",
      "iam:ListAttachedRolePolicies",
      "iam:ListInstanceProfilesForRole",
      "iam:ListPolicyVersions",
      "iam:ListRolePolicies",
      "iam:PassRole",
      "iam:PutRolePolicy",
      "iam:TagPolicy",
      "iam:TagRole",
      "iam:UntagPolicy",
      "iam:UntagRole",
      "iam:UpdateRole",
    ]
    resources = ["*"]
  }

  # KMS
  statement {
    sid = "KMS"
    actions = [
      "kms:CreateAlias",
      "kms:CreateKey",
      "kms:Decrypt",
      "kms:DescribeKey",
      "kms:Encrypt",
      "kms:GenerateDataKey",
      "kms:GetKeyPolicy",
      "kms:GetKeyRotationStatus",
      "kms:ListAliases",
      "kms:ListResourceTags",
    ]
    resources = ["*"]
  }

  # S3
  statement {
    sid = "S3"
    actions = [
      "s3:DeleteObject",
      "s3:GetBucketAcl",
      "s3:GetBucketLogging",
      "s3:GetBucketPolicy",
      "s3:GetBucketTagging",
      "s3:GetBucketVersioning",
      "s3:GetEncryptionConfiguration",
      "s3:GetLifecycleConfiguration",
      "s3:GetObject",
      "s3:ListBucket",
      "s3:PutObject",
    ]
    resources = ["*"]
  }

  # SNS
  statement {
    sid = "SNS"
    actions = [
      "sns:CreateTopic",
      "sns:DeleteTopic",
      "sns:GetSubscriptionAttributes",
      "sns:GetTopicAttributes",
      "sns:ListSubscriptionsByTopic",
      "sns:ListTagsForResource",
      "sns:ListTopics",
      "sns:SetTopicAttributes",
      "sns:Subscribe",
      "sns:TagResource",
      "sns:Unsubscribe",
      "sns:UntagResource",
    ]
    resources = ["*"]
  }

  # SSM
  statement {
    sid = "SSM"
    actions = [
      "ssm:AddTagsToResource",
      "ssm:DeleteParameter",
      "ssm:DescribeParameters",
      "ssm:GetParameter",
      "ssm:GetParameters",
      "ssm:GetParametersByPath",
      "ssm:ListTagsForResource",
      "ssm:PutParameter",
      "ssm:RemoveTagsFromResource",
    ]
    resources = ["*"]
  }

  # STS
  statement {
    sid = "STS"
    actions = [
      "sts:GetCallerIdentity",
    ]
    resources = ["*"]
  }

  # Tags
  statement {
    sid = "Tags"
    actions = [
      "tag:GetResources",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "github_actions_tofu" {
  name   = "tofu-plan-apply"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.github_actions_tofu.json
}
