#!/bin/bash

# Run tests from dev-local so my brain stops hurting with paths
cd ..
source ./utility-functions.bash
set -e -u -o pipefail

echo "Checking if Blue Button is running..."

# Check if web service is running
# TODO: Possible to start them intelligently? Attempts were made, but it always tried to /recreate/ web, which would fail to set
# env variables correctly
if ! docker ps --format '{{.Names}}' | grep -q "dev-local.*web"; then
    echo "Blue Button is not running."
	echo "Please start Blue Button before running selenium tests."
	echo "Exiting..."
	exit 1
fi

echo "Blue Button is running. Starting selenium tests..."

echo $(pwd)
# Capture exit code and always cleanup
docker-compose -f selenium/docker-compose-selenium.yaml run --rm selenium-tests
EXIT_CODE=$?

docker-compose -f selenium/docker-compose-selenium.yaml down

exit $EXIT_CODE


# #!/usr/bin/env bash
# # Make paths relative to this script so it can be run from anywhere
# BASEDIR=$(cd "$(dirname "$0")" && pwd)
# source "${BASEDIR}/utility-functions.bash"

# # Set bash builtins for safety
# set -e -u -o pipefail

# display_usage() {
# 		echo
# 		echo "Usage:"
# 		echo "------------------"
# 		echo
# 		echo "  Use one of the following command line options for the type of test to run:" 
# 		echo
# 		echo "    slsx  = use SLSX for identity service."
# 		echo "    mslsx (default) = use MSLSX for identity service."
# 		echo "    account  = test user account management and application management."
# 		echo "    logit  = run integration tests for bb2 loggings, MSLSX used as identity service."
# 		echo
# 		echo "Options:" 
# 		echo
# 		echo "-h     Print this Help."
# 		echo "-g     Selenium grid used - hub on port 4444."
# 		echo "-t     Show test case actions on std out."
# 		echo "-d     Enable debugpy debugging (port 6789)."
# 		echo
# }

# # Defaults
# export USE_MSLSX=true
# export USE_NEW_PERM_SCREEN=true
# export SERVICE_NAME="selenium-tests"
# export TESTS_LIST="./apps/integration_tests/selenium_tests.py"
# export DJANGO_SETTINGS_MODULE="hhs_oauth_server.settings.dev"
# export BB2_SERVER_STD2FILE=""
# export SELENIUM_GRID=false
# PYTEST_SHOW_TRACE_OPT=''
# DEBUG_MODE=false
# DEBUG_CMD=''

# # Where to put temporary certs for mounting into containers
# export CERTSTORE_TEMPORARY_MOUNT_PATH="../dev-local/certstore"

# # Parse options
# while getopts "hgtd" option; do
# 	 case $option in
# 			h)
# 				 display_usage
# 				 exit;;
# 			g)
# 				export SELENIUM_GRID=true;;
# 			t)
# 				export PYTEST_SHOW_TRACE_OPT='-s';;
# 			d)
# 				DEBUG_MODE=true;;
# 		 \?)
# 				 display_usage
# 				 exit;;
# 	 esac
# done

# # Shift to get non-option arguments
# shift $((OPTIND-1))

# last_arg=${1:-}

# # default: msls mock
# set_msls () {
# 		export DJANGO_MEDICARE_SLSX_REDIRECT_URI="http://localhost:8000/mymedicare/sls-callback"
# 		export DJANGO_MEDICARE_SLSX_LOGIN_URI="http://msls:8080/sso/authorize?client_id=bb2api"
# 		export DJANGO_SLSX_HEALTH_CHECK_ENDPOINT="http://msls:8080/health"
# 		export DJANGO_SLSX_TOKEN_ENDPOINT="http://msls:8080/sso/session"
# 		export DJANGO_SLSX_SIGNOUT_ENDPOINT="http://msls:8080/sso/signout"
# 		export DJANGO_SLSX_USERINFO_ENDPOINT="http://msls:8080/v1/users"
# }

# set_slsx () {
# 		export DJANGO_MEDICARE_SLSX_REDIRECT_URI="http://localhost:8000/mymedicare/sls-callback"
# 		export DJANGO_MEDICARE_SLSX_LOGIN_URI="https://test.medicare.gov/sso/authorize?client_id=bb2api"
# 		export DJANGO_SLSX_HEALTH_CHECK_ENDPOINT="https://test.accounts.cms.gov/health"
# 		export DJANGO_SLSX_TOKEN_ENDPOINT="https://test.medicare.gov/sso/session"
# 		export DJANGO_SLSX_SIGNOUT_ENDPOINT="https://test.medicare.gov/sso/signout"
# 		export DJANGO_SLSX_USERINFO_ENDPOINT="https://test.accounts.cms.gov/v1/users"
# }

# # default to msls
# set_msls

# if [ -z "${last_arg}" ]
# then
# 	echo "Use Mock SLS for identity service."
# else
# 	echo ${last_arg}
# 	if [[ ${last_arg} != "slsx" && ${last_arg} != "mslsx" && ${last_arg} != "logit" && ${last_arg} != "account" ]]
# 	then
# 		echo "Invalid argument: " ${last_arg}
# 		display_usage
# 		exit 1
# 	else
# 		if [[ ${last_arg} == "slsx" ]]
# 		then
# 				export USE_MSLSX=false
# 				set_slsx
# 		fi
# 		if [[ ${last_arg} == "logit" ]]
# 		then
# 			rm -rf ./dev-local/tmp/
# 			mkdir -p ./dev-local/tmp
# 			export DJANGO_SETTINGS_MODULE="hhs_oauth_server.settings.logging_it"
# 			export TESTS_LIST="./apps/integration_tests/logging_tests.py::TestLoggings::test_auth_fhir_flows_logging"
# 			export DJANGO_LOG_JSON_FORMAT_PRETTY=False
# 		fi
# 		if [[ ${last_arg} == "account" ]]
# 		then
# 			rm -rf ./dev-local/tmp/
# 			mkdir -p ./dev-local/tmp
# 			export BB2_SERVER_STD2FILE="YES"
# 			export DJANGO_SETTINGS_MODULE="hhs_oauth_server.settings.logging_it"
# 			export TESTS_LIST="./apps/integration_tests/selenium_accounts_tests.py::TestUserAndAppMgmt::testAccountAndAppMgmt"
# 			export DJANGO_LOG_JSON_FORMAT_PRETTY=False
# 		fi
# 	fi
# fi

# echo "DJANGO_SETTINGS_MODULE: " ${DJANGO_SETTINGS_MODULE}
# echo "TARGET ENV: " ${TARGET_ENV:-dev}
# echo "HOSTNAME_URL: " ${HOSTNAME_URL:-http://localhost:8000}
# echo "Selenium grid=" ${SELENIUM_GRID}
# echo "Debug mode=" ${DEBUG_MODE}

# # Ensure certstore exists
# if [ -d "${CERTSTORE_TEMPORARY_MOUNT_PATH}" ]
# then
# 		echo_msg
# 		echo_msg "  - OK: The temporary certstore mount path is found at: ${CERTSTORE_TEMPORARY_MOUNT_PATH}"
# else
# 		mkdir -p ${CERTSTORE_TEMPORARY_MOUNT_PATH}
# 		echo_msg
# 		echo_msg "  - OK: Created the temporary certstore mount path at: ${CERTSTORE_TEMPORARY_MOUNT_PATH}"
# fi

# # NOTE: At this stage we do not automatically fetch cert/key files from AWS Secrets Manager.
# # If you need to run against remote `test` or `sbx` environments, this script can be extended to
# # call the secret-manager via `aws secretsmanager get-secret-value` like the original script did.
# # That logic is intentionally omitted for fully-local runs using `msls`.

# # If debug mode requested, set debug command
# if [ "$DEBUG_MODE" = true ]; then
# 		DEBUG_CMD="python3 -m debugpy --listen 0.0.0.0:6789 --wait-for-client -m "
# 		echo_msg "DEBUG MODE ENABLED - Debugger will wait for client on port 6789"
# fi

# # Bring up and run the tests in the dev-local compose
# echo_msg "Running Selenium tests using docker-compose..."

# docker compose -f dev-local/docker-compose.selenium.yml down --remove-orphans || true

# docker compose -f dev-local/docker-compose.selenium.yml run --service-ports ${SERVICE_NAME} bash -c "DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE} SELENIUM_GRID=${SELENIUM_GRID} ${DEBUG_CMD}pytest ${PYTEST_SHOW_TRACE_OPT} ${TESTS_LIST}"

# # Stop containers after use
# echo_msg
# echo_msg "Stopping containers..."
# echo_msg

# docker compose -f dev-local/docker-compose.selenium.yml stop || true

# echo_msg
# echo_msg "Shred and Remove certfiles from CERTSTORE_TEMPORARY_MOUNT_PATH=${CERTSTORE_TEMPORARY_MOUNT_PATH}"
# echo_msg

# if which shred >/dev/null 2>&1
# then
# 		echo_msg "  - Shredding files"
# 		shred "${CERTSTORE_TEMPORARY_MOUNT_PATH}/ca.cert.pem" || true
# 		shred "${CERTSTORE_TEMPORARY_MOUNT_PATH}/ca.key.nocrypt.pem" || true
# fi

# echo_msg "  - Removing files"
# rm -f "${CERTSTORE_TEMPORARY_MOUNT_PATH}/ca.cert.pem" || true
# rm -f "${CERTSTORE_TEMPORARY_MOUNT_PATH}/ca.key.nocrypt.pem" || true

# echo_msg "All done."

