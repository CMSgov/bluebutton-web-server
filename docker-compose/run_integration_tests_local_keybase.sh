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
if [[ $1 != "local" && $1 != "local-debug" && $1 != "dc" && $1 != "dc-debug" && $1 != "cbc" ]]
then
  echo
  echo "COMMAND USAGE HELP"
  echo "------------------"
  echo
  echo "  Use one of the following command line options for the type of test to run:"
  echo
  echo "    local  = Run using the docker-compose web local developer setup + local bfd (QUICK test)"
  echo
  echo "    local-debug  = Same as 'local' with tests run waiting on port 6789 to be attached"
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

if [[ $1 == "local" || $1 == "local-debug" ]]
then
  echo "Extracting local BFD trusted client cert and private key files in .pem format."
  
  BFD_REPO=${BFD_REPO:-'../beneficiary-fhir-data'}
  
  BFD_CLIENT_TRUSTED_PFX="${BFD_REPO}/apps/bfd-server/dev/ssl-stores/client-trusted-keystore.pfx"
  
  if [ ! -z ${BFD_CLIENT_TRUSTED_PFX} ] && [ -f ${BFD_CLIENT_TRUSTED_PFX} ]
  then
      if ! command -v openssl &> /dev/null
      then
          echo "openssl command not found, it is needed to extract local BFD trusted client cert and key files in .pem format"
          echo " from client-trusted-keystore.pfx in local bfd repo, please install openssl or manually obtain them and put under"
          echo " bluebutton server certstore (default location: ./docker-compose/certstore/), for details check: ./docker-compose/certstore/README.md"
          exit 127
      fi
  else
      echo "${BFD_CLIENT_TRUSTED_PFX} not found, it is required to extract client trusted pfx."
      exit 127
  fi

  FHIR_URL="https://192.168.0.109:1337"
  CERT_FILENAME="ca.cert.pem"
  KEY_FILENAME="ca.key.nocrypt.pem"
  CERTSTORE_TEMPORARY_MOUNT_PATH="./docker-compose/certstore"
  openssl pkcs12 -in ${BFD_CLIENT_TRUSTED_PFX} -password pass:changeit -nocerts -out "${CERTSTORE_TEMPORARY_MOUNT_PATH}/${KEY_FILENAME}" -nodes
  openssl pkcs12 -in ${BFD_CLIENT_TRUSTED_PFX} -password pass:changeit -nokeys -out "${CERTSTORE_TEMPORARY_MOUNT_PATH}/${CERT_FILENAME}"

  if [ ! -z "${DEBUG_OPTS}" ]
  then
    echo "Integration tests run in debug mode, waiting on port ${EXPO_PORTS} for attach..."
  fi
  docker-compose run ${EXPO_PORTS} -e FHIR_URL=${FHIR_URL} -e HOSTNAME_URL=${HOSTNAME_URL} \
    web bash -c "python ${DEBUG_OPTS} runtests.py --integration ${INTEGRATION_TESTS_LIST}"
else
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
    # Stop web if running and restart db
    docker-compose stop web
    docker-compose restart db

    # Run docker-compose containter one-off
    echo_msg
    echo_msg "------RUNNING DOCKER-COMPOSE CONTAINER WITH INTEGRATION TESTS------"
    echo_msg
    echo_msg "    INTEGRATION_TESTS_LIST: ${INTEGRATION_TESTS_LIST}"
    echo_msg

    if [[ ${SYSTEM} == "Linux" || ${SYSTEM} == "Darwin" ]]
    then
      docker-compose run \
        --service-ports \
        -e DJANGO_FHIR_CERTSTORE=${DJANGO_FHIR_CERTSTORE} \
        -e DJANGO_USER_ID_ITERATIONS=${DJANGO_USER_ID_ITERATIONS} \
        -e DJANGO_USER_ID_SALT=${DJANGO_USER_ID_SALT} \
        -e FHIR_URL=${FHIR_URL} \
        -e HOSTNAME_URL=${HOSTNAME_URL} \
        -v "${CERTSTORE_TEMPORARY_MOUNT_PATH}:${DJANGO_FHIR_CERTSTORE}" \
        web bash -c "python runtests.py --integration ${INTEGRATION_TESTS_LIST}"
    else
      if [ ! -z "${DEBUG_OPTS}" ]
      then
        echo "Integration tests run in debug mode, waiting on port ${EXPO_PORTS} for attach..."
      fi
      docker-compose run ${EXPO_PORTS} \
        -e DJANGO_FHIR_CERTSTORE=${DJANGO_FHIR_CERTSTORE} \
        -e DJANGO_USER_ID_ITERATIONS=${DJANGO_USER_ID_ITERATIONS} \
        -e DJANGO_USER_ID_SALT=${DJANGO_USER_ID_SALT} \
        -e FHIR_URL=${FHIR_URL} \
        -e HOSTNAME_URL=${HOSTNAME_URL} \
        web bash -c "python ${DEBUG_OPTS} runtests.py --integration ${INTEGRATION_TESTS_LIST}"
    fi
  fi

  # Check if tests are to run in docker CBC container one-off
  if [[ $1 == "cbc" ]]
  then
    echo_msg
    echo_msg "------RUNNING DOCKER CONTAINER CBC IMAGE WITH INTEGRATION TESTS------"
    echo_msg
    echo_msg "    INTEGRATION_TESTS_LIST: ${INTEGRATION_TESTS_LIST}"
    echo_msg
    docker run \
      -e DJANGO_USER_ID_SALT=${DJANGO_USER_ID_SALT} \
      -e DJANGO_USER_ID_ITERATIONS=${DJANGO_USER_ID_ITERATIONS} \
      -e DJANGO_FHIR_CERTSTORE=${DJANGO_FHIR_CERTSTORE} \
      -e FHIR_URL=${FHIR_URL} \
      --env-file ${keybase_env} \
      --mount type=bind,source="$(pwd)",target=/app,readonly \
      --mount type=bind,source="${CERTSTORE_TEMPORARY_MOUNT_PATH}",target=/certstore,readonly \
      --rm \
      ${DOCKER_IMAGE}:${DOCKER_TAG} bash -c "cd /app; \
                                            pip install -r requirements/requirements.txt \
                                                          --no-index --find-links ./vendor/; \
                                            pip install sqlparse; \
                                            python runtests.py --integration ${INTEGRATION_TESTS_LIST}"
  fi
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
