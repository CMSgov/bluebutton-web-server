#!/usr/bin/env bash

# It is assumed that the Makefile was invoked with 
#
# ENV=test 
#
# or
#
# ENV=sbx
# in order to get here. Or, you could run this directly with
#
# ENV=test ./retrieve-certs.bash 
# 
# or similar, for testing.

./check-env-preconditions.bash

# We have to grab the right secret. 
# We use a suffix on a base path for that.
if [ "${ENV}" = "local" ]; then
    echo "Running locally. Not retrieving certs."
    exit 0
elif [ "${ENV}" = "test" ]; then
    export SUFFIX="_test"
elif [ "${ENV}" = "sbx" ]; then
    export SUFFIX=""
else
    echo "ENV must be set to 'test' or 'sbx'."
    echo "ENV is currently set to '${ENV}'."
    echo "Exiting."
    exit -2
fi 


# We will (rudely) create a .bb2 directory in the user's homedir.
# Let's call that BB2_CONFIG_DIR
export BB2_CONFIG_DIR="${HOME}/.bb2"
mkdir -p "${BB2_CONFIG_DIR}"
# And, lets put the certs in their own subdir.
export BB2_CERTSTORE="${BB2_CONFIG_DIR}/certstore"
mkdir -p "${BB2_CERTSTORE}"

echo "Retrieving certs for the '${ENV}' environment."
aws secretsmanager get-secret-value --secret-id /bb2/local_integration_tests/fhir_client/certstore/local_integration_tests_certificate${SUFFIX} --query 'SecretString' --output text | base64 -d > "${BB2_CERTSTORE}/ca.cert.pem"

if [ $? -ne 0 ]; then
    echo "Failed to retrieve cert. Exiting."
    exit -3
fi

aws secretsmanager get-secret-value --secret-id /bb2/local_integration_tests/fhir_client/certstore/local_integration_tests_private_key${SUFFIX} --query 'SecretString' --output text | base64 -d > "${BB2_CERTSTORE}/ca.key.nocrypt.pem"

if [ $? -ne 0 ]; then 
    echo "Failed to retrieve private key. Exiting."
    exit -4
fi

echo "Retrieved cert and key for '${ENV}'."