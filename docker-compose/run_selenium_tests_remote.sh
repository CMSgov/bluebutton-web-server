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
    echo "Usage:"
    echo "------------------"
    echo
    echo "Syntax: run_selenium_tests_remote.sh [-h|d] [SBX|PROD|TEST|<bb2 server url>]"
    echo
    echo "Options:"
    echo
    echo "-h     Print this Help."
    echo "-d     Run tests in selenium debug mode (vnc view web UI interaction at http://localhost:5900)."
    echo
    echo "Examples:"
    echo
    echo "run_selenium_tests_remote.sh  https://sandbox.bluebutton.cms.gov/ (or SBX)"
    echo
    echo "run_selenium_tests_remote.sh  https://api.bluebutton.cms.gov/ (or PROD)"
    echo
    echo "run_selenium_tests_remote.sh  https://test.bluebutton.cms.gov/ (or TEST)"
    echo
    echo "<bb2 server url> default to SBX (https://sandbox.bluebutton.cms.gov/)"
    echo
    echo
}

# main
echo_msg
echo_msg RUNNING SCRIPT:  ${0}
echo_msg

# Set bash builtins for safety
set -e -u -o pipefail

export USE_DEBUG=false
export SERVICE_NAME="selenium-tests-remote"
export TESTS_LIST="./apps/integration_tests/selenium_tests.py"
# BB2 service end point default (SBX)
export HOSTNAME_URL="https://sandbox.bluebutton.cms.gov/"
export USE_DEBUG=false

while getopts "hd" option; do
   case $option in
      h)
        display_usage;
        exit;;
      d)
        export USE_DEBUG=true;
        shift;break;;
     \?)
        display_usage;
        exit;;
   esac
done

if [[ -n ${1-''} ]]
then
    case "$1" in
        SBX)
            export HOSTNAME_URL="https://sandbox.bluebutton.cms.gov/"
            ;;
        PROD)
            export HOSTNAME_URL="https://api.bluebutton.cms.gov/"
            ;;
        TEST)
            export HOSTNAME_URL="https://test.bluebutton.cms.gov/"
            ;;
        *)
            if [[ $1 == 'http*' ]]
            then
                export HOSTNAME_URL=$1
            else
                echo "Invalid argument: " $1
                display_usage
                exit 1
            fi
            ;;
    esac
fi

# Set SYSTEM
SYSTEM=$(uname -s)

echo "USE_DEBUG=" ${USE_DEBUG}
echo "BB2 Server URL=" ${HOSTNAME_URL}

export USE_DEBUG
export USE_MSLSX=false

# stop all before run selenium remote tests
docker-compose -f docker-compose.selenium.remote.yml down --remove-orphans

if $USE_DEBUG
then
    docker-compose -f docker-compose.selenium.remote.yml run selenium-remote-tests-debug bash -c "pytest ${TESTS_LIST}"
else
    docker-compose -f docker-compose.selenium.remote.yml run selenium-remote-tests bash -c "pytest ${TESTS_LIST}"
fi

# Stop containers after use
echo_msg
echo_msg "Stopping containers..."
echo_msg

docker-compose -f docker-compose.selenium.remote.yml stop
