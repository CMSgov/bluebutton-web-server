#!/bin/bash

# Run the unit tests in a docker container.
#
# This is for testing using the docker CBC (Cloud Bees Core) containter image
# that is utilized for CBC/Github PR checks.
# 
DOCKER_IMAGE="public.ecr.aws/f5g8o1y9/bb2-cbc-build"
DOCKER_TAG="py36-an27-tf11"

# Set bash builtins for safety
set -e -u -o pipefail

# Echo function that includes script name on each line for console log readability
echo_msg () {
  echo "$(basename $0): $*"
}

# main
echo_msg
echo_msg RUNNING SCRIPT:  ${0}
echo_msg

# Tests are to run in a docker CBC container one-off
echo_msg
echo_msg "------RUNNING DOCKER CONTAINER CBC IMAGE WITH UNIT TESTS------"
echo_msg
docker run \
      --mount type=bind,source="$(pwd)",target=/app \
      --rm \
      ${DOCKER_IMAGE}:${DOCKER_TAG} bash -c "cd /app; \
                                            make reqs-install; \
                                            make reqs-install-dev; \
                                            python runtests.py"
