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
    echo "Syntax: run_selenium_tests_remote.sh [-h|d|p] [SBX|PROD|TEST|<bb2 server url>]"
    echo
    echo "Options:"
    echo
    echo "-h     Print this Help."
    echo "-p     Test for newer permissions screen. Defaults to older screen."
    echo "-g     Selenium grid used."
    echo "-t     Show test case actions on std out."
    echo
    echo "Examples:"
    echo
    echo "run_selenium_tests_remote.sh -p https://sandbox.bluebutton.cms.gov/ (or SBX)"
    echo
    echo "run_selenium_tests_remote.sh  https://api.bluebutton.cms.gov/ (or PROD)"
    echo
    echo "run_selenium_tests_remote.sh -p  https://test.bluebutton.cms.gov/ (or TEST)"
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

export USE_NEW_PERM_SCREEN=false
export SERVICE_NAME="selenium-tests-remote"
# TODO optionally add the Spanish selenium tests here if desired
export TESTS_LIST="./apps/integration_tests/selenium_tests.py ./apps/integration_tests/selenium_spanish_tests.py"
# BB2 service end point default (SBX)
export HOSTNAME_URL="https://sandbox.bluebutton.cms.gov/"
# selenium grid
export SELENIUM_GRID=false
# Show test actions on std out : pytest -s
PYTEST_SHOW_TRACE_OPT=''

while getopts "hpgt" option; do
   case $option in
      h)
        display_usage;
        exit;;
      p)
        export USE_NEW_PERM_SCREEN=true;;
      g)
        export SELENIUM_GRID=true;;
      t)
        export PYTEST_SHOW_TRACE_OPT='-s';;
     \?)
        display_usage;
        exit;;
   esac
done

eval last_arg=\$$#

echo "last arg: " $last_arg

if [[ -n ${last_arg} ]]
then
    case "${last_arg}" in
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
            if [[ ${last_arg} == 'http'* ]]
            then
                export HOSTNAME_URL=${last_arg}
            else
                echo "Invalid argument: " ${last_arg}
                display_usage
                exit 1
            fi
            ;;
    esac
fi

# Set SYSTEM
SYSTEM=$(uname -s)

echo "USE_NEW_PERM_SCREEN=" ${USE_NEW_PERM_SCREEN}
echo "BB2 Server URL=" ${HOSTNAME_URL}
echo "Selenium grid=" ${SELENIUM_GRID}

## export USE_NEW_PERM_SCREEN
export USE_MSLSX=false

# stop all before run selenium remote tests
docker-compose -f docker-compose.selenium.remote.yml down --remove-orphans
docker-compose -f docker-compose.selenium.remote.yml run selenium-remote-tests bash -c "SELENIUM_GRID=${SELENIUM_GRID} pytest ${PYTEST_SHOW_TRACE_OPT} ${TESTS_LIST}"

# Stop containers after use
echo_msg
echo_msg "Stopping containers..."
echo_msg

docker-compose -f docker-compose.selenium.remote.yml stop
