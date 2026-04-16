#!/usr/bin/env bash
# =============================================================================
# ECS Environment Discovery
# Fargate equivalent of inventory/aws_ec2.yaml in bluebutton-web-deployment.
#
# 
# This:    Discovers ECS cluster/service/network by environment name + convention
#
# Usage (in GitHub Actions):
#   source ops/ecs-discover.sh <environment> [service_key]
#
# Outputs (exported env vars):
#   ECS_CLUSTER      e.g. bb-test-cluster
#   ECS_SERVICE      e.g. bb-test-api-service
#   ECS_FAMILY       e.g. bb-test-api  (task definition family, no revision)
#   ECS_CONTAINER    e.g. bb-test-api
#   ECS_NET_CONFIG   JSON network configuration from the running service
# =============================================================================

set -euo pipefail

ENV="${1:?Usage: source ops/ecs-discover.sh <environment> [service_key]}"
SERVICE_KEY="${2:-api}"

APP="bb"
ECS_CLUSTER="${APP}-${ENV}-cluster"
ECS_SERVICE="${APP}-${ENV}-${SERVICE_KEY}-service"
ECS_CONTAINER="${APP}-${ENV}-${SERVICE_KEY}"

echo "Discovering ECS environment: cluster=${ECS_CLUSTER} service=${ECS_SERVICE}"

# Validate cluster is ACTIVE
# Mirrors aws_ec2.yaml filter: instance-state-name: running
CLUSTER_STATUS=$(aws ecs describe-clusters \
  --clusters "${ECS_CLUSTER}" \
  --query 'clusters[0].status' \
  --output text 2>/dev/null || echo "MISSING")

if [[ "${CLUSTER_STATUS}" != "ACTIVE" ]]; then
  echo "ERROR: Cluster ${ECS_CLUSTER} not found or not ACTIVE (status=${CLUSTER_STATUS})" >&2
  exit 1
fi

# Get network configuration from the running service
# Subnets and security groups are managed by CMS Cloud — we read them at runtime
ECS_NET_CONFIG=$(aws ecs describe-services \
  --cluster "${ECS_CLUSTER}" \
  --services "${ECS_SERVICE}" \
  --query 'services[0].networkConfiguration' \
  --output json)

if [[ "${ECS_NET_CONFIG}" == "null" || -z "${ECS_NET_CONFIG}" ]]; then
  echo "ERROR: Service ${ECS_SERVICE} not found in cluster ${ECS_CLUSTER}" >&2
  exit 1
fi

# Extract task definition family (strips the revision suffix)
# e.g. arn:.../bb-test-api:12  ->  bb-test-api
ECS_FAMILY=$(aws ecs describe-services \
  --cluster "${ECS_CLUSTER}" \
  --services "${ECS_SERVICE}" \
  --query 'services[0].taskDefinition' \
  --output text | awk -F/ '{print $NF}' | awk -F: '{print $1}')

if [[ -z "${ECS_FAMILY}" || "${ECS_FAMILY}" == "None" ]]; then
  echo "ERROR: Could not determine task definition family for ${ECS_SERVICE}" >&2
  exit 1
fi

echo "Discovered: cluster=${ECS_CLUSTER} service=${ECS_SERVICE} family=${ECS_FAMILY} container=${ECS_CONTAINER}"

export ECS_CLUSTER ECS_SERVICE ECS_FAMILY ECS_CONTAINER ECS_NET_CONFIG
