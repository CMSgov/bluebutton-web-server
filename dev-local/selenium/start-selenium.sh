#!/usr/bin/env bash

# This script runs inside the selenium docker container, at the moment it only runs locally and sets up a 
# socat relay, but this should be put behind a conditional if TARGET_ENV is 'local'

source /code/dev-local/utility-functions.bash

echo_msg ""
echo_msg "DJANGO_SETTINGS_MODULE: " ${DJANGO_SETTINGS_MODULE}
echo_msg "TARGET ENV: " ${TARGET_ENV}
echo_msg "HOSTNAME_URL: " ${HOSTNAME_URL}
echo_msg "SELENIUM GRID: " ${SELENIUM_GRID}
echo_msg "USE MSLSX: " ${USE_MSLSX}
echo_msg "DEBUG: " ${DEBUG_MODE}
echo_msg "PERMISSION SCREEN: " ${USE_NEW_PERM_SCREEN}
echo_msg 

set_slsx () {
		export DJANGO_MEDICARE_SLSX_LOGIN_URI="https://test.medicare.gov/sso/authorize?client_id=bb2api"
		export DJANGO_SLSX_HEALTH_CHECK_ENDPOINT="https://test.accounts.cms.gov/health"
		export DJANGO_SLSX_TOKEN_ENDPOINT="https://test.medicare.gov/sso/session"
		export DJANGO_SLSX_SIGNOUT_ENDPOINT="https://test.medicare.gov/sso/signout"
		export DJANGO_SLSX_USERINFO_ENDPOINT="https://test.accounts.cms.gov/v1/users"
}

set_msls () {
		export DJANGO_MEDICARE_SLSX_LOGIN_URI="http://msls:8080/sso/authorize?client_id=bb2api"
		export DJANGO_SLSX_HEALTH_CHECK_ENDPOINT="http://msls:8080/health"
		export DJANGO_SLSX_TOKEN_ENDPOINT="http://msls:8080/sso/session"
		export DJANGO_SLSX_SIGNOUT_ENDPOINT="http://msls:8080/sso/signout"
		export DJANGO_SLSX_USERINFO_ENDPOINT="http://msls:8080/v1/users"
}

# Start socat proxy
socat TCP-LISTEN:8000,fork,reuseaddr TCP:host.docker.internal:8000 &
echo_msg "Started localhost:8000 proxy to host"

if [ "$USE_MSLSX" = true ]; then
    set_msls
else
    set_slsx
fi

if [ "$DEBUG_MODE" = true ]; then
    DEBUG_CMD="python3 -m debugpy --listen 0.0.0.0:6789 --wait-for-client -m "
    echo_msg "DEBUG MODE ENABLED - Debugger waiting on 0.0.0.0:6789"
fi

${DEBUG_CMD}pytest -s --tb=line ./apps/integration_tests/selenium_tests.py ./apps/integration_tests/selenium_spanish_tests.py ${PYTEST_SHOW_TRACE_OPT}
# bash "DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE} SELENIUM_GRID=${SELENIUM_GRID} ${DEBUG_CMD}pytest ${PYTEST_SHOW_TRACE_OPT} ${TESTS_LIST}"

