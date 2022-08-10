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

# Backend FHIR server to use for selenium tests with FHIR requests:
FHIR_URL="https://prod-sbx.bfd.cms.gov"

export DJANGO_SETTINGS_MODULE="hhs_oauth_server.settings.logging_it"

# Echo function that includes script name on each line for console log readability
echo_msg () {
    echo "$(basename $0): $*"
}

# main
echo_msg
echo_msg RUNNING SCRIPT:  ${0}
echo_msg

# Set bash builtins for safety
set -e -u -o pipefail

export USE_MSLSX=true
export USE_DEBUG=false
export SERVICE_NAME="selenium-tests"
export TESTS_LIST="apps.integration_tests.selenium_tests.SeleniumTests"
export DJANGO_MEDICARE_SLSX_REDIRECT_URI="http://bb2slsx:8000/mymedicare/sls-callback"
export DJANGO_MEDICARE_SLSX_LOGIN_URI="http://msls:8080/sso/authorize?client_id=bb2api"
export DJANGO_SLSX_HEALTH_CHECK_ENDPOINT="http://msls:8080/health"
export DJANGO_SLSX_TOKEN_ENDPOINT="http://msls:8080/sso/session"
export DJANGO_SLSX_SIGNOUT_ENDPOINT="http://msls:8080/sso/signout"
export DJANGO_SLSX_USERINFO_ENDPOINT="http://msls:8080/v1/users"

# Parse command line option
if [ $# -eq 0 ]
then
  echo "Use MSLSX for identity service."
else
  if [[ $1 != "slsx" && $1 != "mslsx" && $1 != "slsx-debug" && $1 != "mslsx-debug" && $1 != "debug" && $1 != "logit" ]]
  then
    echo
    echo "COMMAND USAGE HELP"
    echo "------------------"
    echo
    echo "  Use one of the following command line options for the type of test to run:"
    echo
    echo "    slsx  = use SLSX for identity service with webdriver in headless mode."
    echo
    echo "    slsx-debug  = use SLSX for identity service, and start selenium standalone chrome debug mode (visualized browser interactions)."
    echo
    echo "    mslsx (default) = use MSLSX for identity service with webdriver in headless mode."
    echo
    echo "    mslsx-debug = use MSLSX for identity service with selenium chrome standalone debug mode."
    echo
    echo "    debug = same as 'mslsx-debug'"
    echo
    echo "    logit  = run integration tests for bb2 loggings, MSLSX used as identity service."
    echo
    exit 1
  else
    if [[ $1 == *debug ]]
    then
        export USE_DEBUG=true
        export SERVICE_NAME="selenium-tests-debug"
    fi
    if [[ $1 == "slsx" || $1 == "slsx-debug" ]]
    then
      export USE_MSLSX=false
      export DJANGO_MEDICARE_SLSX_REDIRECT_URI="http://bb2slsx:8000/mymedicare/sls-callback"
      export DJANGO_MEDICARE_SLSX_LOGIN_URI="https://test.medicare.gov/sso/authorize?client_id=bb2api"
      export DJANGO_SLSX_HEALTH_CHECK_ENDPOINT="https://test.accounts.cms.gov/health"
      export DJANGO_SLSX_TOKEN_ENDPOINT="https://test.medicare.gov/sso/session"
      export DJANGO_SLSX_SIGNOUT_ENDPOINT="https://test.medicare.gov/sso/signout"
      export DJANGO_SLSX_USERINFO_ENDPOINT="https://test.accounts.cms.gov/v1/users"
    fi
    if [[ $1 == "logit" ]]
    then
      export TESTS_LIST="apps.integration_tests.logging_tests.LoggingTests.test_auth_fhir_flows_logging"
      export DJANGO_LOG_JSON_FORMAT_PRETTY=False
    fi
  fi
fi

echo "DJANGO_SETTINGS_MODULE: " ${DJANGO_SETTINGS_MODULE}
echo "HOSTNAME_URL: " ${HOSTNAME_URL}

# Set SYSTEM
SYSTEM=$(uname -s)

# Source ENVs
# BFD prod-sbx settings
export DJANGO_USER_ID_SALT=$(aws ssm get-parameters --names /bb2/test/app/django_user_id_salt --query "Parameters[].Value" --output text --with-decryption)
export DJANGO_USER_ID_ITERATIONS=$(aws ssm get-parameters --names /bb2/test/app/django_user_id_iterations --query "Parameters[].Value" --output text --with-decryption)

# SLSx test env settings
export DJANGO_SLSX_CLIENT_ID=$(aws ssm get-parameters --names /bb2/test/app/slsx_client_id --query "Parameters[].Value" --output text --with-decryption)
export DJANGO_SLSX_CLIENT_SECRET=$(aws ssm get-parameters --names /bb2/test/app/slsx_client_secret --query "Parameters[].Value" --output text --with-decryption)
export DJANGO_PASSWORD_HASH_ITERATIONS=$(aws ssm get-parameters --names /bb2/test/app/django_password_hash_iterations --query "Parameters[].Value" --output text --with-decryption)

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
aws secretsmanager get-secret-value --secret-id /bb2/local_integration_tests/fhir_client/certstore/local_integration_tests_certificate --query 'SecretString' --output text |base64 -d > ${CERTSTORE_TEMPORARY_MOUNT_PATH}/ca.cert.pem
aws secretsmanager get-secret-value --secret-id /bb2/local_integration_tests/fhir_client/certstore/local_integration_tests_private_key --query 'SecretString' --output text |base64 -d > ${CERTSTORE_TEMPORARY_MOUNT_PATH}/ca.key.nocrypt.pem

# stop all before run selenium tests
docker-compose -f docker-compose.selenium.yml down --remove-orphans

export DJANGO_USER_ID_SALT=${DJANGO_USER_ID_SALT}
export DJANGO_USER_ID_ITERATIONS=${DJANGO_USER_ID_ITERATIONS}
export DJANGO_PASSWORD_HASH_ITERATIONS=${DJANGO_PASSWORD_HASH_ITERATIONS}
export DJANGO_SLSX_CLIENT_ID=${DJANGO_SLSX_CLIENT_ID}
export DJANGO_SLSX_CLIENT_SECRET=${DJANGO_SLSX_CLIENT_SECRET}

echo "Selenium tests ..."
echo "MSLSX=" ${USE_MSLSX}
echo "DEBUG=" ${USE_DEBUG}
echo "SERVICE NAME=" ${SERVICE_NAME}

docker-compose -f docker-compose.selenium.yml run ${SERVICE_NAME} bash -c "python runtests.py --selenium ${TESTS_LIST}"

# Stop containers after use
echo_msg
echo_msg "Stopping containers..."
echo_msg

docker-compose -f docker-compose.selenium.yml stop

# Remove certfiles from local directory
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
