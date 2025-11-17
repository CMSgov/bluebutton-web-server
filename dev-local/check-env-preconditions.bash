#!/usr/bin/env bash

if [ "${ENV}" != "local" ]; then
    if [ -z ${KION_ACCOUNT_ALIAS} ]; then
        echo "You must run 'kion f BB2_NON_PROD' before 'make run ENV=test'."
        echo "Exiting."
    fi
fi

# https://stackoverflow.com/questions/3601515/how-to-check-if-a-variable-is-set-in-bash
if [ -z ${ENV} ]; then
    echo "ENV not set. Cannot retrieve certs."
    echo "ENV must be one of 'local', 'test', or 'sbx'."
    echo "For example:"
    echo "  make run-local ENV=test"
    echo "Exiting."
    exit -1
fi
