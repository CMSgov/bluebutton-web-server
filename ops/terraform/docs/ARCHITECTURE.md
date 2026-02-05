# Architecture Overview: Blue Button API


This document provides a visual and technical overview of the **Terraservice** architecture for the Blue Button API deployment.

## Infrastructure Overview

The following diagram shows the complete infrastructure including external services (Akamai CDN), runtime components (ECS/Fargate), and CI/CD pipeline (GitHub Actions):

![Overall Architecture](images/overall_architecture.png)

### Traffic Flow
- **User Traffic**: User → Akamai CDN → VPN/Akamai Security Groups → ALB → ECS Fargate
- **CI/CD Pipeline**: GitHub → GitHub Actions (OIDC) → CodeBuild → ECR Repository
- **Runtime Dependencies**: ECS Tasks pull images from ECR, secrets from Secrets Manager, config from SSM

---

## Infrastructure Diagram (Detailed Mermaid)

```mermaid
graph TD
    classDef external fill:#f9f,stroke:#333,stroke-width:2px;
    classDef network fill:#bbf,stroke:#333,stroke-width:2px;
    classDef compute fill:#dfd,stroke:#333,stroke-width:2px;
    classDef storage fill:#ffd,stroke:#333,stroke-width:2px;
    classDef security fill:#fcc,stroke:#333,stroke-width:2px;

    User((User)) -->|HTTPS:443| Akamai["Akamai CDN"]
    Akamai -->|HTTPS:443| SG_ALB["Security Groups<br/>(VPN + Akamai)"]
    SG_ALB --> ALB["Application Load Balancer"]

    subgraph "VPC (Managed by bb-platform)"
        ALB
        subgraph "Private Subnets"
            API["ECS Fargate Tasks (api:8000)"]
        end
    end

    ALB -->|HTTPS:8000| API

    API -.->|Pull Image| ECR["ECR Repository"]
    API -.->|Get Secrets| SM["Secrets Manager"]
    API -.->|Get Config| SSM["SSM Parameter Store"]
    API -.->|Logging| CWL["CloudWatch Logs"]

    subgraph "CI/CD (bb-codebuild)"
        GHA["GitHub Actions"] -->|OIDC| IAM["IAM Role"]
        GHA -->|Webhook| CB["CodeBuild Runner"]
        CB -->|Push| ECR
    end

    class Akamai external;
    class User external;
    class ALB network;
    class API,CB compute;
    class ECR,SM,SSM,CWL storage;
    class SG_ALB security;
```

---

## ECS Module Structure

The following diagram shows how the Terraform resources in the `bb-ecs` module are organized and how they depend on each other:

![ECS Terraform Structure](images/ecs_terraform_structure.png)

**Key Resource Flow:**
1. **Data Sources** (green): Discover secrets from Secrets Manager and configuration from SSM
2. **Core Infrastructure** (blue): ECS Cluster with Fargate capacity providers
3. **Service Layer** (blue): Task Definitions inject secrets/env vars, Services reference the cluster
4. **Supporting Resources** (orange/blue): IAM roles, Security Groups, ALB, ECR, CloudWatch

---

## Pattern Overview: Terraservice

The infrastructure is built using three primary modules:

### 1. [bb-platform](../modules/bb-platform/platform.tf)
*   **Purpose**: Discovers existing environment resources and loads configuration.
*   **Responsibilities**: VPC/Subnet lookup, ACM Certificate resolution, KMS Key discovery, and SSM Parameter loading.
*   **Output**: A consolidated `platform` object passed to application modules.

### 2. [bb-ecs](../modules/bb-ecs/main.tf)
*   **Purpose**: Provisions the application-specific compute and networking.
*   **Responsibilities**: ECS Cluster, Fargate Service, Target Groups, Security Groups, and IAM Roles.
*   **Security**: ALB restricted to VPN/Akamai security groups; ECS accepts traffic only from ALB on port 8000.

### 3. [bb-codebuild](../modules/bb-codebuild/main.tf)
*   **Purpose**: CI/CD infrastructure for GitHub Actions integration.
*   **Responsibilities**: CodeBuild project (GitHub Actions runner), ECR repository, GitHub OIDC provider, IAM roles.
*   **Integration**: Automatically triggered by GitHub Actions via webhook.

---

## Security Group Flow

```
Internet → Akamai CDN → VPN/Akamai SGs → ALB (443) → ECS SG (8000) → ECS Tasks
```

| Security Group | Purpose |
|----------------|---------|
| `cmscloud-vpn` | CMS VPN access |
| `bb-sg-{env}-clb-cms-vpn` | Environment-specific VPN |
| `bb-sg-{env}-clb-akamai-prod` | Akamai CDN traffic |
| `bb-{env}-api-alb-sg` | ALB ingress (references above SGs) |
| `bb-{env}-ecs-api-sg` | ECS ingress (from ALB only) |

---

## Log & Metric Flow

1.  **Container Logs**: Forwarded via `awslogs` driver to CloudWatch.
2.  **Performance Metrics**: Collected via CloudWatch Container Insights (Cluster level).
3.  **ALB Logs**: Sent to Environment-specific S3 bucket for audit and debugging.
4.  **CodeBuild Logs**: `/aws/codebuild/bb-{env}-web-server` in CloudWatch.

