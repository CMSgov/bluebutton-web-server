#!/usr/bin/env bash

# This script runs inside the selenium docker container, at the moment it only runs locally and sets up a 
# socat relay, but this should be put behind a conditional if TARGET_ENV is 'local'

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

set_msls () {
		export DJANGO_MEDICARE_SLSX_LOGIN_URI="http://localhost:8080/sso/authorize?client_id=bb2api"
		export DJANGO_SLSX_HEALTH_CHECK_ENDPOINT="http://localhost:8080/health"
		export DJANGO_SLSX_TOKEN_ENDPOINT="http://localhost:8080/sso/session"
		export DJANGO_SLSX_SIGNOUT_ENDPOINT="http://localhost:8080/sso/signout"
		export DJANGO_SLSX_USERINFO_ENDPOINT="http://localhost:8080/v1/users"
}

# BB2 runs with network_mode: host on the Podman/Docker machine.
# The selenium compose project has its own isolated bridge network whose gateway
# does NOT route to the host-networked BB2. host.docker.internal (the machine
# gateway) reaches host ports from any network, so proxy BB2 traffic through it.
BB2_HOST="host.docker.internal"
echo_msg "BB2 host resolved to: ${BB2_HOST}"

# Start socat proxy - forward localhost ports to BB2 on the host
socat TCP-LISTEN:8000,fork,reuseaddr TCP:${BB2_HOST}:8000 &
socat TCP-LISTEN:8080,fork,reuseaddr TCP:${BB2_HOST}:8080 &
echo_msg "Started localhost port proxy to BB2 at ${BB2_HOST}"

# Chrome runs in this container's network namespace (network_mode: service:selenium-tests).
# Wait for its Selenium Grid to be ready before pytest starts.
export SELENIUM_GRID_HOST=localhost
echo_msg "Waiting for Chrome Selenium Grid on localhost:4444..."
for i in $(seq 1 30); do
    if python3 -c "import socket; s=socket.socket(); s.settimeout(2); s.connect(('localhost', 4444)); s.close()" 2>/dev/null; then
        echo_msg "Chrome Selenium Grid is ready"
        break
    fi
    sleep 2
    if [ "$i" -eq 30 ]; then
        echo_msg "Timeout: Chrome Selenium Grid not ready after 60s"
        exit 1
    fi
done

if [ "$USE_MSLSX" = true ]; then
    set_msls
else
    set_slsx
fi

if [ "$DEBUG_MODE" = true ]; then
    DEBUG_CMD="python3 -m debugpy --listen 0.0.0.0:7890 --wait-for-client -m "
    echo_msg "DEBUG MODE ENABLED - Debugger waiting on 0.0.0.0:7890"
fi

${DEBUG_CMD}pytest -s --tb=line ./apps/integration_tests/selenium_tests.py ./apps/integration_tests/selenium_spanish_tests.py ${PYTEST_SHOW_TRACE_OPT}
# bash "DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE} SELENIUM_GRID=${SELENIUM_GRID} ${DEBUG_CMD}pytest ${PYTEST_SHOW_TRACE_OPT} ${TESTS_LIST}"

