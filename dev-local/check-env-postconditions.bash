#!/usr/bin/env bash

./check-env-preconditions.bash

echo "Checking postconditions."

if [ "${ENV}" != "local" ]; then
    # Check that one of our DJANGO values are populated.
    if [ -z ${DJANGO_SLSX_CLIENT_ID} ]; then
        echo "Failed to source salt/client values. Exiting."
        exit -2
    fi
fi

echo "All systems go."