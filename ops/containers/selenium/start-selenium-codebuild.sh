#!/usr/bin/env bash

# This script runs inside the selenium docker container for codebuild environments.
# Unlike the local version, it does NOT use socat relays since containers communicate
# directly via docker networking.

source /code/ops/containers/selenium/utility-functions.bash

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

if [ "$USE_MSLSX" = true ]; then
    # In codebuild, MSLSX would need to be available on the network
    export DJANGO_MEDICARE_SLSX_LOGIN_URI="http://mslsx:8080/sso/authorize?client_id=bb2api"
    export DJANGO_SLSX_HEALTH_CHECK_ENDPOINT="http://mslsx:8080/health"
    export DJANGO_SLSX_TOKEN_ENDPOINT="http://mslsx:8080/sso/session"
    export DJANGO_SLSX_SIGNOUT_ENDPOINT="http://mslsx:8080/sso/signout"
    export DJANGO_SLSX_USERINFO_ENDPOINT="http://mslsx:8080/v1/users"
else
    set_slsx
fi

DEBUG_CMD=""
if [ "$DEBUG_MODE" = true ]; then
    DEBUG_CMD="python3 -m debugpy --listen 0.0.0.0:7890 --wait-for-client -m "
    echo_msg "DEBUG MODE ENABLED - Debugger waiting on 0.0.0.0:7890"
fi

${DEBUG_CMD}pytest -s --tb=line ./apps/integration_tests/selenium_tests.py ./apps/integration_tests/selenium_spanish_tests.py ${PYTEST_SHOW_TRACE_OPT}
