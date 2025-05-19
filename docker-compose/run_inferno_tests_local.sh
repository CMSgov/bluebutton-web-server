#!/bin/bash

# Run the selenium tests in docker
#
# NOTE:
#
#   1. You must be logged in to AWS CLI.
#
#   2. You must also be connected to the VPN.
#
# SETTINGS:  You may need to customize these for your local setup.

export CERTSTORE_TEMPORARY_MOUNT_PATH="./docker-compose/certstore"
export DJANGO_FHIR_CERTSTORE="/code/docker-compose/certstore"

# BB2 service end point default
export HOSTNAME_URL="http://bb2slsx:8000"

# Echo function that includes script name on each line for console log readability
echo_msg () {
    echo "$(basename $0): $*"
}

display_usage() {
    echo
    echo "Usage:"
    echo "------------------"
    echo
    echo "Options:"
    echo
    echo "-h     Print this Help."
    echo "-p     Use new permissions screen (defaults to old style screen)."
    echo "-g     Selenium grid used - hub on port 4444."
    echo "-t     Show test case actions on std out."
    echo
}

# set up using SLSX
set_slsx () {
    export DJANGO_MEDICARE_SLSX_REDIRECT_URI="http://bb2slsx:8000/mymedicare/sls-callback"
    export DJANGO_MEDICARE_SLSX_LOGIN_URI="https://test.medicare.gov/sso/authorize?client_id=bb2api"
    export DJANGO_SLSX_HEALTH_CHECK_ENDPOINT="https://test.accounts.cms.gov/health"
    export DJANGO_SLSX_TOKEN_ENDPOINT="https://test.medicare.gov/sso/session"
    export DJANGO_SLSX_SIGNOUT_ENDPOINT="https://test.medicare.gov/sso/signout"
    export DJANGO_SLSX_USERINFO_ENDPOINT="https://test.accounts.cms.gov/v1/users"
}

# set up using mock sls
set_msls () {
    export DJANGO_MEDICARE_SLSX_REDIRECT_URI="http://bb2slsx:8000/mymedicare/sls-callback"
    export DJANGO_MEDICARE_SLSX_LOGIN_URI="http://msls:8080/sso/authorize?client_id=bb2api"
    export DJANGO_SLSX_HEALTH_CHECK_ENDPOINT="http://msls:8080/health"
    export DJANGO_SLSX_TOKEN_ENDPOINT="http://msls:8080/sso/session"
    export DJANGO_SLSX_SIGNOUT_ENDPOINT="http://msls:8080/sso/signout"
    export DJANGO_SLSX_USERINFO_ENDPOINT="http://msls:8080/v1/users"
}

# main
echo_msg
echo_msg RUNNING SCRIPT:  ${0}
echo_msg

# Set bash builtins for safety
set -e -u -o pipefail

export USE_MSLSX=true
export USE_NEW_PERM_SCREEN=false
export TESTS_LIST="./apps/integration_tests/selenium_inferno_tests.py"
export DJANGO_SETTINGS_MODULE="hhs_oauth_server.settings.dev"
export BB2_SERVER_STD2FILE=""
# selenium grid
export SELENIUM_GRID=false
# Show test actions on std out : pytest -s
PYTEST_SHOW_TRACE_OPT=''

# this seems been overridden by set_msls below - comment out for removal
# set_slsx

# Parse command line option
while getopts "hpgt" option; do
   case $option in
      h)
         display_usage
         exit;;
      p)
         export USE_NEW_PERM_SCREEN=true;;
      g)
        export SELENIUM_GRID=true;;
      t)
        export PYTEST_SHOW_TRACE_OPT='-s';;
     \?)
         display_usage
         exit;;
   esac
done

eval last_arg=\$$#

# the default is to use mock login - e.g. for account mgmt tests and logging integration tests
set_msls

# Parse command line option
if [ $# -eq 0 ]
then
  echo "Use Mock SLS for identity service."
else
fi

echo "DJANGO_SETTINGS_MODULE: " ${DJANGO_SETTINGS_MODULE}
echo "HOSTNAME_URL: " ${HOSTNAME_URL}
echo "Selenium grid=" ${SELENIUM_GRID}

# Set SYSTEM
SYSTEM=$(uname -s)

# Source ENVs
# BFD prod-sbx settings
export DJANGO_USER_ID_SALT=$(aws secretsmanager get-secret-value --secret-id /bb2/test/app/django_user_id_salt --query 'SecretString' --output text)
export DJANGO_USER_ID_ITERATIONS=$(aws secretsmanager get-secret-value --secret-id /bb2/test/app/django_user_id_iterations --query 'SecretString' --output text)

# value cleansing of trailing \r on cygwin
export DJANGO_USER_ID_SALT=${DJANGO_USER_ID_SALT//$'\r'}
export DJANGO_USER_ID_ITERATIONS=${DJANGO_USER_ID_ITERATIONS//$'\r'}

# SLSx test env settings
export DJANGO_SLSX_CLIENT_ID=$(aws secretsmanager get-secret-value --secret-id /bb2/test/app/slsx_client_id --query 'SecretString' --output text)
export DJANGO_SLSX_CLIENT_SECRET=$(aws secretsmanager get-secret-value --secret-id /bb2/test/app/slsx_client_secret --query 'SecretString' --output text)
export DJANGO_PASSWORD_HASH_ITERATIONS=$(aws secretsmanager get-secret-value --secret-id /bb2/test/app/django_password_hash_iterations --query 'SecretString' --output text)

# Inferno test app creds
export DJANGO_CLIENT_ID_4_INFERNO_TEST=''
export DJANGO_CLIENT_SECRET_4_INFERNO_TEST=''

# value cleansing of trailing \r on cygwin
export DJANGO_SLSX_CLIENT_ID=${DJANGO_SLSX_CLIENT_ID//$'\r'}
export DJANGO_SLSX_CLIENT_SECRET=${DJANGO_SLSX_CLIENT_SECRET//$'\r'}
export DJANGO_PASSWORD_HASH_ITERATIONS=${DJANGO_PASSWORD_HASH_ITERATIONS//$'\r'}

# Check ENV vars have been sourced
if [ -z "${DJANGO_USER_ID_SALT}" ]
then
    echo_msg "ERROR: The DJANGO_USER_ID_SALT variable was not sourced!"
    exit 1
fi
if [ -z "${DJANGO_USER_ID_ITERATIONS}" ]
then
    echo_msg "ERROR: The DJANGO_USER_ID_ITERATIONS variable was not sourced!"
    exit 1
fi

# Check temp certstore dir and create if not existing
if [ -d "${CERTSTORE_TEMPORARY_MOUNT_PATH}" ]
then
    echo_msg
    echo_msg "  - OK: The temporary certstore mount path is found at: ${CERTSTORE_TEMPORARY_MOUNT_PATH}"
else
    mkdir ${CERTSTORE_TEMPORARY_MOUNT_PATH}
    echo_msg
    echo_msg "  - OK: Created the temporary certstore mount path at: ${CERTSTORE_TEMPORARY_MOUNT_PATH}"
fi


# Copy certfiles from AWS Secrets Manager to local for container mount
echo_msg "  - COPY certfiles from AWS Secrets Manager to local temp for container mount..."
echo_msg

if [[ ${SYSTEM} == "Linux" || ${SYSTEM} == "Darwin" ]]
then
    aws secretsmanager get-secret-value --secret-id /bb2/local_integration_tests/fhir_client/certstore/local_integration_tests_certificate --query 'SecretString' --output text |base64 -d > ${CERTSTORE_TEMPORARY_MOUNT_PATH}/ca.cert.pem
    aws secretsmanager get-secret-value --secret-id /bb2/local_integration_tests/fhir_client/certstore/local_integration_tests_private_key --query 'SecretString' --output text |base64 -d > ${CERTSTORE_TEMPORARY_MOUNT_PATH}/ca.key.nocrypt.pem
else
    # support cygwin
    aws secretsmanager get-secret-value --secret-id /bb2/local_integration_tests/fhir_client/certstore/local_integration_tests_certificate --query 'SecretString' --output text |base64 -di > ${CERTSTORE_TEMPORARY_MOUNT_PATH}/ca.cert.pem
    aws secretsmanager get-secret-value --secret-id /bb2/local_integration_tests/fhir_client/certstore/local_integration_tests_private_key --query 'SecretString' --output text |base64 -di > ${CERTSTORE_TEMPORARY_MOUNT_PATH}/ca.key.nocrypt.pem
fi

# stop all before run selenium tests
docker compose -f docker-compose.inferno.yml down --remove-orphans

export DJANGO_USER_ID_SALT=${DJANGO_USER_ID_SALT}
export DJANGO_USER_ID_ITERATIONS=${DJANGO_USER_ID_ITERATIONS}
export DJANGO_PASSWORD_HASH_ITERATIONS=${DJANGO_PASSWORD_HASH_ITERATIONS}
export DJANGO_SLSX_CLIENT_ID=${DJANGO_SLSX_CLIENT_ID}
export DJANGO_SLSX_CLIENT_SECRET=${DJANGO_SLSX_CLIENT_SECRET}

echo "Selenium Inferno tests ..."
echo "MSLSX=" ${USE_MSLSX}
echo "USE_NEW_PERM_SCREEN=" ${USE_NEW_PERM_SCREEN}

docker compose -f docker-compose.inferno.yml run inferno-local-tests bash -c "DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE} SELENIUM_GRID=${SELENIUM_GRID} pytest ${PYTEST_SHOW_TRACE_OPT} ${TESTS_LIST}"

#Stop containers after use
echo_msg
echo_msg "Stopping containers..."
echo_msg

docker compose -f docker-compose.inferno.yml stop

#Remove certfiles from local directory
echo_msg
echo_msg Shred and Remove certfiles from CERTSTORE_TEMPORARY_MOUNT_PATH=${CERTSTORE_TEMPORARY_MOUNT_PATH}
echo_msg

if which shred
then
    echo_msg "  - Shredding files"
    shred "${CERTSTORE_TEMPORARY_MOUNT_PATH}/ca.cert.pem"
    shred "${CERTSTORE_TEMPORARY_MOUNT_PATH}/ca.key.nocrypt.pem"
fi

echo_msg "  - Removing files"
rm "${CERTSTORE_TEMPORARY_MOUNT_PATH}/ca.cert.pem"
rm "${CERTSTORE_TEMPORARY_MOUNT_PATH}/ca.key.nocrypt.pem"
