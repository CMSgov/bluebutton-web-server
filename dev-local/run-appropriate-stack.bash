#!/usr/bin/env bash
source ./utility-functions.bash

# this says to "export all variables."
set -a
# exit on error.
set -e

# bfd = local | test | sbx
# auth = mock | live

# let's make sure we have a valid ENV var before proceeding
check_valid_env

# source the baseline environment variables
# these set the stage for all further environment manipulation for 
# launching the app.
clear_canary_variables
source ./.env.local

# add another check or two after we source the env file.
check_env_after_source

# let's make sure the .env.local sourced in correctly.
check_env_preconditions

# set the FHIR_URL and FHIR_URL_V3
set_bfd_urls

# set the profile for docker compose
set_auth_profile

# retrieve the certs and store them in $HOME/.bb2/certstore
retrieve_certs

set_salt

echo "🚀 Launching the stack for '${bfd}/${auth}'."

if [[ "${bfd}" == "local" ]]; then
    echo "🥶 FHIR_URLs are not set when running locally."
    echo "   BFD calls will fail."
else
    echo "FHIR_URLs are:"
    echo "  * ${FHIR_URL}"
    echo "  * ${FHIR_URL_V3}"
fi

cleanup_docker_stack

if [[ "${daemon}" == "1" ]]; then
    docker compose \
    -f docker-compose-local.yaml \
    up \
    --detach
else
    echo "📊 Tailing logs."
    echo
    docker compose \
        -f docker-compose-local.yaml \
        up
fi
