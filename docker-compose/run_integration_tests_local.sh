#!/bin/bash

# Run the integration tests in:
#
#   * a one-off docker (cbc) or
#   * docker-compose (dc) container or
#   * docker-compose container with local bfd as backend
#
# NOTE:
#
#   When backend is a remote BFD, e.g. production/sandbox:
#
#   1. You must be logged in to AWS CLI.
#
#   2. You must also be connected to the VPN.
#
#   When backend is a local bfd, 1. and 2. are not required

# SETTINGS:  You may need to customize these for your local setup.
HOSTNAME_URL="http://localhost:8000"

DJANGO_FHIR_CERTSTORE="/certstore"
CERTSTORE_TEMPORARY_MOUNT_PATH="/tmp/certstore"

DOCKER_IMAGE="public.ecr.aws/f5g8o1y9/bb2-cbc-build"
#DOCKER_TAG="py36-an27-tf11"
DOCKER_TAG="py37-an27-tf12-boto3-botocore"

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

# Set SYSTEM
SYSTEM=$(uname -s)

# Set bash builtins for safety
set -e -u -o pipefail

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
    # bc or dc mode
    # BFD prod-sbx settings
    export DJANGO_USER_ID_SALT=$(aws ssm get-parameters --names /bb2/test/app/django_user_id_salt --query "Parameters[].Value" --output text --with-decryption)
    export DJANGO_USER_ID_ITERATIONS=$(aws ssm get-parameters --names /bb2/test/app/django_user_id_iterations --query "Parameters[].Value" --output text --with-decryption)

    # cleansing trailing \r on cygwin
    export DJANGO_USER_ID_SALT=${DJANGO_USER_ID_SALT//$'\r'}
    export DJANGO_USER_ID_ITERATIONS=${DJANGO_USER_ID_ITERATIONS//$'\r'}

    # SLSx test env settings
    export DJANGO_SLSX_CLIENT_ID=$(aws ssm get-parameters --names /bb2/test/app/slsx_client_id --query "Parameters[].Value" --output text --with-decryption)
    export DJANGO_SLSX_CLIENT_SECRET=$(aws ssm get-parameters --names /bb2/test/app/slsx_client_secret --query "Parameters[].Value" --output text --with-decryption)
    export DJANGO_PASSWORD_HASH_ITERATIONS=$(aws ssm get-parameters --names /bb2/test/app/django_password_hash_iterations --query "Parameters[].Value" --output text --with-decryption)

    # cleansing trailing \r on cygwin
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
            # cygwin
            docker-compose run ${EXPO_PORTS} \
                -e DJANGO_FHIR_CERTSTORE="/code/docker-compose${DJANGO_FHIR_CERTSTORE}" \
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
        aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws/f5g8o1y9
        docker run \
            -e DJANGO_USER_ID_SALT=${DJANGO_USER_ID_SALT} \
            -e DJANGO_USER_ID_ITERATIONS=${DJANGO_USER_ID_ITERATIONS} \
            -e DJANGO_SLSX_CLIENT_ID=${DJANGO_SLSX_CLIENT_ID} \
            -e DJANGO_SLSX_CLIENT_SECRET=${DJANGO_SLSX_CLIENT_SECRET} \
            -e DJANGO_PASSWORD_HASH_ITERATIONS=${DJANGO_PASSWORD_HASH_ITERATIONS} \
            -e DJANGO_FHIR_CERTSTORE=${DJANGO_FHIR_CERTSTORE} \
            -e FHIR_URL=${FHIR_URL} \
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
