#!/bin/bash

# Source ENV secrets for BFD & SLSx, and copy certfiles to local development
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

# Echo function that includes script name on each line for console log readability
echo_msg () {
    echo "$(basename $0): $*"
}

# main

# Set bash builtins for safety
set -e -u -o pipefail

echo_msg " - Sourcing ENV secrets from: AWS Secrets Manager"
echo_msg

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

# Set SYSTEM
SYSTEM=$(uname -s)

if [[ ${SYSTEM} == "Linux" || ${SYSTEM} == "Darwin" ]]
then
    aws secretsmanager get-secret-value --secret-id /bb2/local_integration_tests/fhir_client/certstore/local_integration_tests_certificate --query 'SecretString' --output text | base64 -d > ${CERTSTORE_TEMPORARY_MOUNT_PATH}/ca.cert.pem
    aws secretsmanager get-secret-value --secret-id /bb2/local_integration_tests/fhir_client/certstore/local_integration_tests_private_key --query 'SecretString' --output text | base64 -d > ${CERTSTORE_TEMPORARY_MOUNT_PATH}/ca.key.nocrypt.pem
else
    # support cygwin
    aws secretsmanager get-secret-value --secret-id /bb2/local_integration_tests/fhir_client/certstore/local_integration_tests_certificate --query 'SecretString' --output text |base64 -di > ${CERTSTORE_TEMPORARY_MOUNT_PATH}/ca.cert.pem
    aws secretsmanager get-secret-value --secret-id /bb2/local_integration_tests/fhir_client/certstore/local_integration_tests_private_key --query 'SecretString' --output text |base64 -di > ${CERTSTORE_TEMPORARY_MOUNT_PATH}/ca.key.nocrypt.pem
fi
