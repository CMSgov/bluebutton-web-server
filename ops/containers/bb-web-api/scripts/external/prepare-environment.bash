#!/usr/bin/env bash
source bb-web-api/scripts/external/prepare-environment-support.bash

####################################
# OPERATING CONDITIONS
# We want bash to fail fast if something goes wrong.
# And, we want all our variables exported so the 
# container launch can pick them up.
set -e
set -a

echo "-------- ENV VARS --------"
echo "🥑 bfd          ${bfd}"
echo "🥑 auth         ${auth}"
echo "🥑 env          ${env}"
echo "🥑 TARGET_ENV   ${TARGET_ENV}"


####################################
# ENV SETUP
check_valid_env
gonogo "check_valid_env"
check_env_preconditions
gonogo "check_env_preconditions"
# source the baseline environment variables
load_env_vars
gonogo "load_env_vars"
check_env_after_setup
gonogo "check_env_after_setup"
set_bfd_urls
gonogo "set_bfd_urls"

####################################
# CERTS
# retrieve the certs for BFD and store them in $BFD_CERT_PEM_B64 and $BFD_KEY_PEM_B64
# We don't write them to disk; that happens *inside* the container.
retrieve_bfd_certs
gonogo "retrieve_bfd_certs"

####################################
# SLSX
# We may want to run against a mock, or against
# the live system. 
configure_slsx

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

# This is run from a makefile two levels up.
# We `cd` into this directory to run the script.
# Hence, we need to pop back up in order to get to the right
# place to run the compose.
cd ../..

if [[ "${daemon}" == "1" ]]; then
    docker compose \
    -f ops/containers/docker-compose-local.yaml \
    up \
    --detach
elif [[ "${MIGRATE}" == "1"  ]]; then
    echo "📊 Migrating."
    echo
    docker compose \
        -f ops/containers/docker-compose-local.yaml \
        up --abort-on-container-exit
    docker compose down
    exit
elif [[ "${COLLECTSTATIC}" == "1" ]]; then
    echo "📊 Collecting static."
    echo
    docker compose \
        -f ops/containers/docker-compose-local.yaml \
        up --abort-on-container-exit
    docker compose down
    exit
else
    echo "📊 Tailing logs."
    echo
    BUILD_TARGET=local \
    RELEASE_TAG=local \
    TARGET_ENV="local" \
    docker compose \
        -f ops/containers/docker-compose-local.yaml \
        up --abort-on-container-exit
fi
