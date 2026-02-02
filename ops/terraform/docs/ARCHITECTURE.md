# Architecture Overview: Blue Button API


This document provides a visual and technical overview of the **Terraservice** architecture for the Blue Button API deployment.

## Infrastructure Diagram

```mermaid
graph TD
    classDef external fill:#f9f,stroke:#333,stroke-width:2px;
    classDef network fill:#bbf,stroke:#333,stroke-width:2px;
    classDef compute fill:#dfd,stroke:#333,stroke-width:2px;
    classDef storage fill:#ffd,stroke:#333,stroke-width:2px;

    User((User)) -->|HTTPS:443| Akamai["Akamai Content Delivery"]
    Akamai -->|HTTPS:443| ALB["Application Load Balancer"]

    subgraph "VPC (Managed by bb-platform)"
        ALB
        subgraph "Private Subnets"
            API["ECS Fargate Tasks (api)"]
        end
    end

    ALB -->|HTTPS:Health Check| API
    ALB -->|HTTPS:Traffic| API

    API -.->|Pull Image| ECR["ECR Repository"]
    API -.->|Get Secrets| SM["Secrets Manager"]
    API -.->|Get Config| SSM["SSM Parameter Store"]
    API -.->|Storage/Config| S3["S3 Buckets"]
    API -.->|Logging| CWL["CloudWatch Logs"]

    class Akamai external;
    class User external;
    class ALB network;
    class API compute;
    class ECR,SM,SSM,S3,CWL storage;
```

---

## Pattern Overview: Terraservice

The infrastructure is built using two primary modules designed to separate foundation from application logic:

### 1. [bb-platform](../modules/bb-platform/platform.tf)
*   **Purpose**: Discovers existing environment resources and loads configuration.
*   **Responsibilities**: VPC/Subnet lookup, ACM Certificate resolution, KMS Key discovery, and SSM Parameter loading.
*   **Output**: A consolidated `platform` object passed to application modules.

### 2. [bb-ecs](../modules/bb-ecs/main.tf)
*   **Purpose**: Provisions the application-specific compute and networking.
*   **Responsibilities**: ECS Cluster, Fargate Service, Target Groups, Security Groups, and IAM Roles.
*   **Security**: Enforces end-to-end **HTTPS-only** (443) for both public and internal traffic.

---

## Log & Metric Flow

1.  **Container Logs**: Forwarded via `awslogs` driver to CloudWatch.
2.  **Performance Metrics**: Collected via CloudWatch Container Insights (Cluster level).
3.  **ALB Logs**: Sent to Environment-specific S3 bucket for audit and debugging.
