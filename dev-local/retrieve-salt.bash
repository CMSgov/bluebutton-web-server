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
# ENV=test source retrieve-salt.bash 
# 
# or similar, for testing.

./check-env-preconditions.bash

if [ "${ENV}" = "local" ]; then
    echo "Running locally. Not retrieving salt."
    return 0
elif [ "${ENV}" = "test" ]; then
    echo "Retrieving salt/client values for '${ENV}'."
elif [ "${ENV}" = "sbx" ]; then
    echo "Retrieving salt/client values for '${ENV}'."
else
    echo "ENV must be set to 'test' or 'sbx'."
    echo "ENV is currently set to '${ENV}'."
    echo "Exiting."
    exit -2
fi

# These seem to be the same regardless of the env (test or sbx).
export DJANGO_USER_ID_SALT=$(aws secretsmanager get-secret-value --secret-id /bb2/test/app/django_user_id_salt --query 'SecretString' --output text)
export DJANGO_USER_ID_ITERATIONS=$(aws secretsmanager get-secret-value --secret-id /bb2/test/app/django_user_id_iterations --query 'SecretString' --output text)
export DJANGO_SLSX_CLIENT_ID=$(aws secretsmanager get-secret-value --secret-id /bb2/test/app/slsx_client_id --query 'SecretString' --output text)
export DJANGO_SLSX_CLIENT_SECRET=$(aws secretsmanager get-secret-value --secret-id /bb2/test/app/slsx_client_secret --query 'SecretString' --output text)
export DJANGO_PASSWORD_HASH_ITERATIONS=$(aws secretsmanager get-secret-value --secret-id /bb2/test/app/django_password_hash_iterations --query 'SecretString' --output text)

echo "Success."