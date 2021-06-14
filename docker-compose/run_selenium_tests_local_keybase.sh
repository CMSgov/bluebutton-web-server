#!/bin/bash

# Run the selenium tests in docker
# 
# NOTE:
#
#   1. You must be logged in to Keybase and have the BB2 team file system mounted.
#
#   2. You must also be connected to the VPN.
#
# SETTINGS:  You may need to customize these for your local setup.

HOSTNAME_URL="http://bb2:8000"

KEYBASE_ENV_FILE="team/bb20/infrastructure/creds/ENV_secrets_for_local_integration_tests.env"
KEYBASE_CERTFILES_SUBPATH="team/bb20/infrastructure/certs/local_integration_tests/fhir_client/certstore/"

BB20_TEAM_VAULT_PASSFILE="/cygdrive/k/team/bb20/infrastructure/creds/vault_pw.txt"
BB20_DEPLOYMENT_VAULTFILE="../bluebutton-web-deployment/vault/env/test/vault.yml"
BB20_ENABLE_REMOTE_DEBUG=True

DJANGO_FHIR_CERTSTORE="/certstore"
CERTSTORE_TEMPORARY_MOUNT_PATH="/tmp/certstore"
CERT_FILENAME="client_data_server_bluebutton_local_integration_tests_certificate.pem"
KEY_FILENAME="client_data_server_bluebutton_local_integration_tests_private_key.pem"

# Backend FHIR server to use for selenium tests with FHIR requests:
FHIR_URL="https://prod-sbx.bfd.cms.gov"

# List of tests to run. To be passed in to runtests.py.
TESTS_LIST="apps.integration_tests.selenium_tests.SeleniumTests"


# Echo function that includes script name on each line for console log readability
echo_msg () {
  echo "$(basename $0): $*"
}

# main
echo_msg
echo_msg RUNNING SCRIPT:  ${0}
echo_msg

DJANGO_USER_ID_SALT=$(ansible-vault view --vault-password-file=${BB20_TEAM_VAULT_PASSFILE} ${BB20_DEPLOYMENT_VAULTFILE} | grep "^vault_env_django_user_id_salt" | awk '{print $2}')
DJANGO_USER_ID_ITERATIONS=$(ansible-vault view --vault-password-file=${BB20_TEAM_VAULT_PASSFILE} ${BB20_DEPLOYMENT_VAULTFILE} | grep "^vault_env_django_user_id_iterations" | awk '{print $2}')

DJANGO_PASSWORD_HASH_ITERATIONS=$(ansible-vault view --vault-password-file=${BB20_TEAM_VAULT_PASSFILE} ${BB20_DEPLOYMENT_VAULTFILE} | grep "^vault_env_django_password_hash_iterations" | awk '{print $2}')
DJANGO_SLSX_CLIENT_ID=$(ansible-vault view --vault-password-file=${BB20_TEAM_VAULT_PASSFILE} ${BB20_DEPLOYMENT_VAULTFILE} | grep "^vault_env_slsx_client_id" | awk '{print $2}')
DJANGO_SLSX_CLIENT_SECRET=$(ansible-vault view --vault-password-file=${BB20_TEAM_VAULT_PASSFILE} ${BB20_DEPLOYMENT_VAULTFILE} | grep "^vault_env_slsx_client_secret" | awk '{print $2}')

# Set bash builtins for safety
set -e -u -o pipefail

# Set KeyBase ENV path based on your type of system
SYSTEM=$(uname -s)

echo_msg " - Setting Keybase location based on SYSTEM type: ${SYSTEM}"
echo_msg

if [[ ${SYSTEM} == "Linux" || ${SYSTEM} == "Darwin" ]]
then
  keybase_env_path="/keybase"
else
  # support cygwin
  keybase_env_path="/cygdrive/k"
  CERTSTORE_TEMPORARY_MOUNT_PATH="./docker-compose/certstore"
  DJANGO_FHIR_CERTSTORE="/code/docker-compose/certstore"
fi

# Keybase ENV file
keybase_env="${keybase_env_path}/${KEYBASE_ENV_FILE}"

echo_msg " - Sourcing ENV secrets from: ${keybase_env}"
echo_msg

# Check that ENV file exists in correct location
if [ ! -f "${keybase_env}" ]
then
echo_msg
echo_msg "ERROR: The ENV secrets could NOT be found at: ${keybase_env}"
echo_msg
exit 1
fi

# Source ENVs
source "${keybase_env}"

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

# Keybase cert files
keybase_certfiles="${keybase_env_path}/${KEYBASE_CERTFILES_SUBPATH}"
keybase_cert_file="${keybase_certfiles}/${CERT_FILENAME}"
keybase_key_file="${keybase_certfiles}/${KEY_FILENAME}"

# Check that certfiles in keybase dir exist
if [ -f "${keybase_cert_file}" ]
then
    echo_msg
    echo_msg "  - OK: The cert file was found at: ${keybase_cert_file}"
else
    echo_msg
    echo_msg "ERROR: The cert file could NOT be found at: ${keybase_cert_file}"
    exit 1
fi

if [ -f ${keybase_key_file} ]
then
    echo_msg
    echo_msg "  - OK: The key file was found at: ${keybase_key_file}"
else
    echo_msg
    echo_msg "ERROR: The key file could NOT be found at: ${keybase_key_file}"
    exit 1
fi

# Copy certfiles from KeyBase to local for container mount
echo_msg "  - COPY certfiles from KeyBase to local temp for container mount..."
echo_msg
cp ${keybase_cert_file} "${CERTSTORE_TEMPORARY_MOUNT_PATH}/ca.cert.pem"
cp ${keybase_key_file} "${CERTSTORE_TEMPORARY_MOUNT_PATH}/ca.key.nocrypt.pem"

# stop all before run selenium tests
docker-compose -f docker-compose.selenium.yml stop

export DJANGO_USER_ID_SALT=${DJANGO_USER_ID_SALT}
export DJANGO_USER_ID_ITERATIONS=${DJANGO_USER_ID_ITERATIONS}
export DJANGO_PASSWORD_HASH_ITERATIONS=${DJANGO_PASSWORD_HASH_ITERATIONS}
export DJANGO_SLSX_CLIENT_ID=${DJANGO_SLSX_CLIENT_ID}
export DJANGO_SLSX_CLIENT_SECRET=${DJANGO_SLSX_CLIENT_SECRET}
export HOSTNAME_URL=${HOSTNAME_URL}

echo "Selenium tests ..."

docker-compose -f docker-compose.selenium.yml run \
-e DJANGO_USER_ID_SALT=${DJANGO_USER_ID_SALT} \
-e DJANGO_USER_ID_ITERATIONS=${DJANGO_USER_ID_ITERATIONS} \
-e DJANGO_PASSWORD_HASH_ITERATIONS=${DJANGO_PASSWORD_HASH_ITERATIONS} \
-e DJANGO_SLSX_CLIENT_ID=${DJANGO_SLSX_CLIENT_ID} \
-e DJANGO_SLSX_CLIENT_SECRET=${DJANGO_SLSX_CLIENT_SECRET} \
-e HOSTNAME_URL=${HOSTNAME_URL} \
tests bash -c "python runtests.py apps.integration_tests.selenium_tests.SeleniumTests"

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
