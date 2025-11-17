#!/usr/bin/env bash

check_valid_env () {
    if [[ "${ENV}" == "local" ]]; then
        # This is a no-op.
        :
    #####
    # TEST
    elif [[ "${ENV}" == "test" ]]; then
        :
    #####
    # SBX
    elif [[ "${ENV}" == "sbx" ]]; then
        :
    #####
    # ERR
    else
        echo "ENV must be set to 'local', 'test', or 'sbx'."
        echo "ENV is currently set to '${ENV}'."
        echo "Exiting."
        exit -2
    fi 

}

check_env_preconditions () {
    if [ "${ENV}" != "local" ]; then
        if [ -z ${KION_ACCOUNT_ALIAS} ]; then
            echo "You must run 'kion f BB2_NON_PROD' before 'make run ENV=test'."
            echo "Exiting."
            return -1
        fi
    fi

    # https://stackoverflow.com/questions/3601515/how-to-check-if-a-variable-is-set-in-bash
    if [ -z ${ENV} ]; then
        echo "ENV not set. Cannot retrieve certs."
        echo "ENV must be one of 'local', 'test', or 'sbx'."
        echo "For example:"
        echo "  make run-local ENV=test"
        echo "Exiting."
        return -1
    fi

    if [ -z ${OAUTHLIB_INSECURE_TRANSPORT} ]; then
        echo "We need insecure transport when running locally."
        echo "OAUTHLIB_INSECURE_TRANSPORT was not set to true."
        echo "Exiting."
        return -1
    fi

    if [ -z ${DB_MIGRATIONS} ]; then
        echo "There should be a DB_MIGRATIONS flag."
        echo "Exiting."
        return -1
    fi
}

