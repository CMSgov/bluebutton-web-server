#!/usr/bin/env bash

# Run tests from dev-local so my brain stops hurting with paths
cd ..
source ./utility-functions.bash
set -a -e -u -o pipefail


export HOSTNAME_URL='http://localhost:8000'
export USE_NEW_PERM_SCREEN='true'
export DJANGO_FHIR_CERTSTORE='/certstore'
export TESTS_LIST='./apps/integration_tests/selenium_tests.py'
export DJANGO_SETTINGS_MODULE='hhs_oauth_server.settings.dev'
export SELENIUM_GRID=true
export PYTEST_SHOW_TRACE_OPT=''

# Currently, you need to stand up your dev environment first and then when you call the selenium tests, you need to match what is running
# otherwise selenium will try and use the wrong login sequence
if [[ "${auth}" == 'live' ]]; then
	export USE_MSLSX=false
	export USE_LOGIN_WITH_MEDICARE_BUTTON=true
else
	export USE_MSLSX=true
	export USE_LOGIN_WITH_MEDICARE_BUTTON=false
fi

# Set debug mode
if [[ "${debug}" == 'true' ]]; then
	export DEBUG_MODE=true
else
	export DEBUG_MODE=false
fi

# Check if web service is running
echo_msg 'Checking if Blue Button is running...'
if ! docker ps --format '{{.Names}}' | grep -q 'dev-local.*web'; then
    echo '\tBlue Button is not running.'
	echo '\tPlease start Blue Button before running selenium tests.'
	echo '\tExiting...'
	exit 1
fi

echo_msg 'Clearing selenium/dump screenshots and html...'

rm -rf selenium/dump

echo_msg 'Blue Button is running. Starting selenium tests...'

docker compose -f selenium/docker-compose-selenium.yaml down --remove-orphans || true

docker compose -f selenium/docker-compose-selenium.yaml run --rm --service-ports selenium-tests
EXIT_CODE=$?

docker compose -f selenium/docker-compose-selenium.yaml down

exit $EXIT_CODE
