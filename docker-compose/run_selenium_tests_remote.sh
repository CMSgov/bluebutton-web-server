#!/bin/bash

# Run the selenium tests against remote bb2 in docker
#
# NOTE:
#
#   1. You must be logged in to AWS CLI.
#
#   2. You must also be connected to the VPN.
#
# SETTINGS:  You may need to customize these for your local setup.

# Echo function that includes script name on each line for console log readability
echo_msg () {
    echo "$(basename $0): $*"
}

display_usage() {
    echo
    echo "USAGE:"
    echo "------------------"
    echo
    echo "Syntax: run_selenium_tests_remote.sh [-h|d] [<bb2 server url>]"
    echo
    echo "Run this script with the URL pointing to the remote BB2 server: e.g."
    echo
    echo "run_selenium_tests_remote.sh  https://sandbox.bluebutton.cms.gov/ this will run selenium tests against the SBX"
    echo
    echo "run_selenium_tests_remote.sh  https://api.bluebutton.cms.gov/ this will run the selenium tests against the PROD"
    echo
    echo "run_selenium_tests_remote.sh  https://test.bluebutton.cms.gov/ this will run the selenium tests against the TEST"
    echo
    echo "options:"
    echo "h     Print this Help."
    echo "d     Run tests in selenium debug mode (vnc view web UI interaction at http://localhost:5900)."
    echo
    echo "<bb2 server url> default to SBX (https://sandbox.bluebutton.cms.gov/)"
}

# main
echo_msg
echo_msg RUNNING SCRIPT:  ${0}
echo_msg

# Set bash builtins for safety
set -e -u -o pipefail

export USE_DEBUG=false
export SERVICE_NAME="selenium-tests-remote"
export TESTS_LIST="apps.integration_tests.selenium_tests.SeleniumTests"
# BB2 service end point default (SBX)
export HOSTNAME_URL="https://sandbox.bluebutton.cms.gov/"

USE_DEBUG=false

# Parse command line option
while getopts ":h" option; do
   case $option in
      h) # display Help
         display_usage
         exit;;
      d) # selenium in debug mode
         USE_DEBUG=true
         exit;;
     \?) # Invalid option
         echo "Error: Invalid option"
         exit;;
   esac
done

if [[ -z ${1-''} ]]
then
    echo "Remote Blue Button Server tested default to SBX: " ${HOSTNAME_URL}
else
    export HOSTNAME_URL=$1
fi

# Set SYSTEM
SYSTEM=$(uname -s)

# creds of the test app registered at target ENV
export TEST_APP_CLIENT_ID=$(aws ssm get-parameters --names /bb2/test/app/test_app_client_id --query "Parameters[].Value" --output text --with-decryption)
export TEST_APP_CLIENT_SECRET=$(aws ssm get-parameters --names /bb2/test/app/test_app_client_secret --query "Parameters[].Value" --output text --with-decryption)

# value cleansing of trailing \r on cygwin
export TEST_APP_CLIENT_ID=${TEST_APP_CLIENT_ID//$'\r'}
export TEST_APP_CLIENT_SECRET=${TEST_APP_CLIENT_SECRET//$'\r'}

# Check target test app's creds are set
if [ -z "${TEST_APP_CLIENT_ID}" ]
then
    echo_msg "ERROR: The required TEST_APP_CLIENT_ID variable was not set!"
    exit 1
fi
if [ -z "${TEST_APP_CLIENT_SECRET}" ]
then
    echo_msg "ERROR: The required TEST_APP_CLIENT_SECRET variable was not set!"
    exit 1
fi

echo "USE_DEBUG=" ${USE_DEBUG}
echo "BB2 Server URL=" ${HOSTNAME_URL}

export USE_DEBUG
export USE_MSLSX=false

# stop all before run selenium remote tests
docker-compose -f docker-compose.selenium.remote.yml down --remove-orphans

if $USE_DEBUG
then
    docker-compose -f docker-compose.selenium.remote.yml run selenium-remote-tests-debug bash -c "python runtests.py --selenium ${TESTS_LIST}"
else
    docker-compose -f docker-compose.selenium.remote.yml run selenium-remote-tests bash -c "python runtests.py --selenium ${TESTS_LIST}"
fi

# Stop containers after use
echo_msg
echo_msg "Stopping containers..."
echo_msg

docker-compose -f docker-compose.selenium.remote.yml stop
