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

if [ "$USE_MSLSX" = true ]; then
    set_msls
else
    set_slsx
fi

DEBUG_CMD=""
if [ "$DEBUG_MODE" = true ]; then
    DEBUG_CMD="python3 -m debugpy --listen 0.0.0.0:7890 --wait-for-client -m "
    echo_msg "DEBUG MODE ENABLED - Debugger waiting on 0.0.0.0:7890"
fi

${DEBUG_CMD}pytest -s --tb=line ./apps/integration_tests/selenium_tests.py ./apps/integration_tests/selenium_spanish_tests.py ${PYTEST_SHOW_TRACE_OPT}
