#!/bin/bash

# Run the inferno tests (selenium based) against BB2 server (LOCAL|PROD/SBX/TEST) 
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
    echo "Syntax: run_inferno_tests.sh [-h|p|g|t] [LOCAL|SBX|PROD|TEST|<bb2 server url>]"
    echo
    echo "Options:"
    echo
    echo "-h     Print this Help."
    echo "-p     Test for newer permissions screen during oauth user login. Defaults to older screen."
    echo "-g     Selenium grid used."
    echo "-t     Show test case actions on std out."
    echo
    echo "Examples:"
    echo
    echo "run_inferno_tests.sh -p https://localhost:8000/ (or LOCAL)"
    echo
    echo "run_inferno_tests.sh -p https://sandbox.bluebutton.cms.gov/ (or SBX)"
    echo
    echo "run_inferno_tests.sh  https://api.bluebutton.cms.gov/ (or PROD)"
    echo
    echo "run_inferno_tests.sh -p  https://test.bluebutton.cms.gov/ (or TEST)"
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

# export INFERNO_URL="http://localhost"
export INFERNO_URL="http://192.168.0.146"
export USE_NEW_PERM_SCREEN=false
export SERVICE_NAME="inferno-tests"
export TESTS_LIST="./apps/integration_tests/selenium_inferno_tests.py"
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
        LOCAL)
            export HOSTNAME_URL="http://localhost:8000/"
            ;;
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

export USE_NEW_PERM_SCREEN
export USE_MSLSX=false

if [[ -n ${last_arg} ]]
then
    case "${last_arg}" in
        LOCAL)
            export HOSTNAME_URL="http://localhost:8000/"
            export DJANGO_CLIENT_ID_4_INFERNO_TEST="client_id_of_built_in_testapp"
            export DJANGO_CLIENT_SECRET_4_INFERNO_TEST="client_secret_of_built_in_testapp"
            ;;
        *)
            # Inferno test app creds
            export DJANGO_CLIENT_ID_4_INFERNO_TEST=$(aws secretsmanager get-secret-value --secret-id /bb2/test/app/inferno_test_client_id --query 'SecretString' --output text)
            export DJANGO_CLIENT_SECRET_4_INFERNO_TEST=$(aws secretsmanager get-secret-value --secret-id /bb2/test/app/inferno_test_client_secret --query 'SecretString' --output text)
            ;;
    esac
fi

# assume the target bb2 server is up, either local or remote
docker compose -f docker-compose.inferno.yml run inferno-tests bash -c "HOSTNAME_URL=${HOSTNAME_URL} CLIENT_ID_4_INFERNO_TEST=${DJANGO_CLIENT_ID_4_INFERNO_TEST} CLIENT_SECRET_4_INFERNO_TEST=${DJANGO_CLIENT_SECRET_4_INFERNO_TEST} INFERNO_URL=${INFERNO_URL} SELENIUM_GRID=${SELENIUM_GRID} pytest ${PYTEST_SHOW_TRACE_OPT} ${TESTS_LIST}"

# Stop containers after use
echo_msg
echo_msg "Stopping containers..."
echo_msg

docker compose -f docker-compose.inferno.yml stop
