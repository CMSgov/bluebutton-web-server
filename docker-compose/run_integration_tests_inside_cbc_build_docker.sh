#!/bin/bash

# This script is called from the deployment repo scripts/cbc-run-integration-tests.sh
# and local development scripts.

# Echo function that includes script name on each line for console log readability
echo_msg () {
  echo "$(basename $0): $1"
}

# main
#set -e
echo_msg "Running script: $0"
echo_msg
echo_msg "  Using ENV/environment variables:"
echo_msg
echo_msg "     BRANCH:  ${BRANCH}"
echo_msg 
echo_msg "     FHIR_URL:  ${FHIR_URL}"

# Clone from local repo if code directory is not found.
if [ ! -d code ]
then
  echo_msg
  echo_msg "- Cloning webserver repo from local mounted /app to code."
  echo_msg
  git clone  /app code
  echo_msg
fi

# Change to code directory.
cd code

# Checkout commit hash or branch if set.
if [[ ${BRANCH} != "" ]]
then
  echo_msg
  echo_msg "- Checkout commit hash or branch from: branch = ${BRANCH}"
  git fetch origin "+refs/heads/master:refs/remotes/origin/master" "+refs/pull/*:refs/remotes/origin/pr/*"
  git checkout "$BRANCH"
fi

# Show git status.
echo_msg
echo_msg "- GIT STATUS:"
git status

echo_msg
echo_msg "- GET Python version info:"
python --version

# Setup Python virtual env.
echo_msg
echo_msg "- Setup Python virtual env and Install requirements:"
python3 -m venv venv
. venv/bin/activate

# Install requirements.
echo_msg
echo_msg "- Setup Python virtual env and Install requirements:"
pip install -r requirements/requirements.txt
pip install sqlparse

# Run integration tests script.
echo_msg
echo_msg "- Running integration tests in StaticLiveServerTestCase mode:"
echo_msg
sh docker-compose/run_integration_tests.sh
result_status=$?

# Return status.
echo_msg
echo_msg
echo_msg "RETURNED: result_status: ${result_status}"
echo_msg
exit ${result_status}
