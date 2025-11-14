#!/usr/bin/env bash

# Exit if any command results in a non-zero exit status.
set -e


docker build \
    --platform "linux/amd64" \
    -t bb-local:latest \
    -f Dockerfile.local ..