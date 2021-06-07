#!/bin/bash

# Run the integration tests in:
#
#   * a one-off docker (cbc) or
#   * docker-compose (dc) container or
#   * docker-compose container with local bfd as backend
# 
# NOTE:
#
#   When backend is a remote BFD, e.g. prodution sandbox:
#
#   1. You must be logged in to Keybase and have the BB2 team file system mounted.
#
#   2. You must also be connected to the VPN.
#
#   When backend is a local bfd, 1. and 2. are not required

# SETTINGS:  You may need to customize these for your local setup.
HOSTNAME_URL="http://localhost:8000"

KEYBASE_ENV_FILE="team/bb20/infrastructure/creds/ENV_secrets_for_local_integration_tests.env"
KEYBASE_CERTFILES_SUBPATH="team/bb20/infrastructure/certs/local_integration_tests/fhir_client/certstore/"

DJANGO_FHIR_CERTSTORE="/certstore"
CERTSTORE_TEMPORARY_MOUNT_PATH="/tmp/certstore"
CERT_FILENAME="client_data_server_bluebutton_local_integration_tests_certificate.pem"
KEY_FILENAME="client_data_server_bluebutton_local_integration_tests_private_key.pem"

DOCKER_IMAGE="public.ecr.aws/f5g8o1y9/bb2-cbc-build"
DOCKER_TAG="py36-an27-tf11"

# Backend FHIR server to use for integration tests of FHIR resource endpoints:
FHIR_URL="https://prod-sbx.bfd.cms.gov"

# List of integration tests to run. To be passed in to runtests.py.
INTEGRATION_TESTS_LIST="apps.integration_tests.integration_test_fhir_resources.IntegrationTestFhirApiResources"


# Echo function that includes script name on each line for console log readability
echo_msg () {
  echo "$(basename $0): $*"
}

# main
echo_msg
echo_msg RUNNING SCRIPT:  ${0}
echo_msg

# Parse command line option
if [[ $1 != "dc" && $1 != "dc-debug" && $1 != "cbc" ]]
then
  echo
  echo "COMMAND USAGE HELP"
  echo "------------------"
  echo
  echo "  Use one of the following command line options for the type of test to run:"
  echo
  echo "    dc  = Run using the docker-compose web local developer setup (QUICK test)"
  echo
  echo "    dc-debug  = Same as 'dc' with tests run waiting on port 5678 to be attached"
  echo
  echo "    cbc = Run using the docker CBC (Cloud Bees Core) containter image (FULL test)"
  echo 
  exit 1
fi

# just silent warnings
export DB_MIGRATIONS=dummy
export SUPER_USER_NAME=dummy
export SUPER_USER_EMAIL=dummy
export SUPER_USER_PASSWORD=dummy
export BB20_ENABLE_REMOTE_DEBUG=dummy
export BB20_REMOTE_DEBUG_WAIT_ATTACH=dummy

BB20_TEAM_VAULT_PASSFILE="/cygdrive/k/team/bb20/infrastructure/creds/vault_pw.txt"
BB20_DEPLOYMENT_VAULTFILE="../bluebutton-web-deployment/vault/env/test/vault.yml"
BB20_ENABLE_REMOTE_DEBUG=True
# If both env vars are not empty (and are set) and both files exist:
# if [ ! -z ${BB20_TEAM_VAULT_PASSFILE} ] && [ ! -z ${BB20_DEPLOYMENT_VAULTFILE} ] && \
#    [ -f ${BB20_TEAM_VAULT_PASSFILE} ] && [ -f ${BB20_DEPLOYMENT_VAULTFILE} ]
# then
echo
echo "INFO: You are using USER_ID SALT/HASH secret values from the vault."
echo "INFO: This is to support the use of HICN/MBI values when testing"
echo "INFO: using the MSLS component for simulating SLS/MyMedicare auth flow."
echo "INFO: Using the following files:"
echo "INFO:    BB20_TEAM_VAULT_PASSFILE: ${BB20_TEAM_VAULT_PASSFILE}"
echo "INFO     BB20_DEPLOYMENT_VAULTFILE: ${BB20_DEPLOYMENT_VAULTFILE}"
echo

DJANGO_USER_ID_SALT=$(ansible-vault view --vault-password-file=${BB20_TEAM_VAULT_PASSFILE} ${BB20_DEPLOYMENT_VAULTFILE} | grep "^vault_env_django_user_id_salt" | awk '{print $2}')
DJANGO_USER_ID_ITERATIONS=$(ansible-vault view --vault-password-file=${BB20_TEAM_VAULT_PASSFILE} ${BB20_DEPLOYMENT_VAULTFILE} | grep "^vault_env_django_user_id_iterations" | awk '{print $2}')

DJANGO_PASSWORD_HASH_ITERATIONS=$(ansible-vault view --vault-password-file=${BB20_TEAM_VAULT_PASSFILE} ${BB20_DEPLOYMENT_VAULTFILE} | grep "^vault_env_django_password_hash_iterations" | awk '{print $2}')
DJANGO_SLSX_CLIENT_ID=$(ansible-vault view --vault-password-file=${BB20_TEAM_VAULT_PASSFILE} ${BB20_DEPLOYMENT_VAULTFILE} | grep "^vault_env_slsx_client_id" | awk '{print $2}')
DJANGO_SLSX_CLIENT_SECRET=$(ansible-vault view --vault-password-file=${BB20_TEAM_VAULT_PASSFILE} ${BB20_DEPLOYMENT_VAULTFILE} | grep "^vault_env_slsx_client_secret" | awk '{print $2}')

# docker-compose stop web
#docker-compose run --service-ports -e DJANGO_USER_ID_SALT=${DJANGO_USER_ID_SALT} -e DJANGO_USER_ID_ITERATIONS=${DJANGO_USER_ID_ITERATIONS} web python3 manage.py runserver 0.0.0.0:8000
#docker-compose run --service-ports -e DJANGO_USER_ID_SALT=${DJANGO_USER_ID_SALT} -e DJANGO_USER_ID_ITERATIONS=${DJANGO_USER_ID_ITERATIONS} web bash -c "if [ ! -d 'bluebutton-css' ] ; then git clone https://github.com/CMSgov/bluebutton-css.git ; else echo 'CSS already installed.' ; fi ; if [ '${BB20_ENABLE_REMOTE_DEBUG}' = true ] ; then python3 -m ptvsd --host 0.0.0.0 --port 5678 manage.py runserver 0.0.0.0:8000 --noreload ; else python3 manage.py runserver 0.0.0.0:8000; fi"
echo "SALT:" ${DJANGO_USER_ID_SALT} ", ITERATIONS:" ${DJANGO_USER_ID_ITERATIONS} 
# docker-compose run --publish 8000:8000 -p 5678:5678 \
# -e DJANGO_USER_ID_SALT=${DJANGO_USER_ID_SALT} \
# -e DJANGO_USER_ID_ITERATIONS=${DJANGO_USER_ID_ITERATIONS} \
# -e DJANGO_PASSWORD_HASH_ITERATIONS=${DJANGO_PASSWORD_HASH_ITERATIONS} \
# -e DJANGO_SLSX_CLIENT_ID=${DJANGO_SLSX_CLIENT_ID} \
# -e DJANGO_SLSX_CLIENT_SECRET=${DJANGO_SLSX_CLIENT_SECRET} \
# web bash -c "if [ ! -d 'bluebutton-css' ] ; then git clone https://github.com/CMSgov/bluebutton-css.git ; else echo 'CSS already installed.' ; fi ; python3 -m debugpy --listen 0.0.0.0:5678 manage.py runserver 0.0.0.0:8000 --noreload"
# fi

# Set bash builtins for safety
set -e -u -o pipefail

# Set KeyBase ENV path based on your type of system
SYSTEM=$(uname -s)

DEBUG_OPTS=""
EXPO_PORTS=""

if [[ $1 == *-debug ]]
then
  DEBUG_OPTS="-m debugpy --listen 0.0.0.0:6789 --wait-for-client"
  EXPO_PORTS="-p 6789:6789"
fi

# cbc or dc mode
echo_msg " - Setting Keybase location based on SYSTEM type: ${SYSTEM}"
echo_msg

if [[ ${SYSTEM} == "Linux" || ${SYSTEM} == "Darwin" ]]
then
keybase_env_path="/keybase"
else
# Assume Windows if not
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

# Check if tests are to run in docker-compose
if [[ $1 == dc* ]]
then
    echo "Selenium tests ..."
    docker-compose -f docker-compose-auto.yml run --publish 8000:8000 -p 5678:5678 \
    -e DJANGO_SETTINGS_MODULE=hhs_oauth_server.settings.dev \
    -e DATABASES_CUSTOM="postgres://postgres:toor@db:5432/bluebutton" \
    -e OAUTHLIB_INSECURE_TRANSPORT=true \
    -e DJANGO_DEFAULT_SAMPLE_FHIR_ID="-20140000008325" \
    -e DJANGO_SECURE_SESSION=False \
    -e DJANGO_FHIR_CERTSTORE="/code/docker-compose/certstore/" \
    -e DJANGO_MEDICARE_SLSX_LOGIN_URI="http://127.0.0.1:8080/sso/authorize?client_id=bb2api" \
    -e DJANGO_MEDICARE_SLSX_REDIRECT_URI="http://localhost:8000/mymedicare/sls-callback" \
    -e DJANGO_SLSX_USERINFO_ENDPOINT="http://msls:8080/v1/users" \
    -e DJANGO_SLSX_HEALTH_CHECK_ENDPOINT="http://msls:8080/health" \
    -e DJANGO_SLSX_TOKEN_ENDPOINT="http://msls:8080/sso/session" \
    -e DJANGO_SLSX_SIGNOUT_ENDPOINT="http://msls:8080/sso/signout" \
    -e DJANGO_SLSX_CLIENT_ID="bb2api" \
    -e DJANGO_SLSX_CLIENT_SECRET=${DJANGO_SLSX_CLIENT_SECRET} \
    -e DJANGO_SLSX_VERIFY_SSL=False \
    -e DJANGO_LOG_JSON_FORMAT_PRETTY=True \
    -e DJANGO_FHIR_CERTSTORE=${DJANGO_FHIR_CERTSTORE} \
    -e DJANGO_USER_ID_ITERATIONS=${DJANGO_USER_ID_ITERATIONS} \
    -e DJANGO_USER_ID_SALT=${DJANGO_USER_ID_SALT} \
    -e FHIR_URL=${FHIR_URL} \
    -e HOSTNAME_URL=${HOSTNAME_URL} \
    web bash -c "python -m debugpy --listen 0.0.0.0:5678 manage.py runserver 0.0.0.0:8000 --noreload"
fi

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
