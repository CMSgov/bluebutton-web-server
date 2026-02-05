[
  {
    "name": "${container_name}",
    "image": "${container_image}",
    "essential": true,
    "entryPoint": ["/usr/local/bin/docker-entrypoint.sh"],
    "portMappings": [
      {
        "containerPort": ${container_port},
        "hostPort": ${container_port},
        "protocol": "tcp"
      }
    ],
    "environment": ${jsonencode(environment)},
    "secrets": ${jsonencode(secrets)},
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "${log_group}",
        "awslogs-region": "${region}",
        "awslogs-stream-prefix": "${container_name}"
      }
    },
    "healthCheck": {
      "command": ["CMD-SHELL", "curl -f http://localhost:${container_port}/health || exit 1"],
      "interval": 30,
      "timeout": 5,
      "retries": 3,
      "startPeriod": 60
    }
  }
]
