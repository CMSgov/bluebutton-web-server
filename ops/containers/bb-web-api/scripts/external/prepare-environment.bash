#!/usr/bin/env bash
source ./prepare-environment-support.bash

####################################
# OPERATING CONDITIONS
# We want bash to fail fast if something goes wrong.
# And, we want all our variables exported so the 
# container launch can pick them up.
set -e
set -a

####################################
# ENV SETUP
check_valid_env
gonogo "check_valid_env"
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
# These are the certs we need for HTTPs termination
# e.g. the things that let us be `test.bluebutton.cms.gov` with secure authority.
# Locally, we create bogus/self-signed certs.
retrieve_nginx_certs
gonogo "retrieve_nginx_certs"

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

if [[ "${daemon}" == "1" ]]; then
    docker compose \
    -f docker-compose-local.yaml \
    up \
    --detach
elif [[ "${MIGRATE}" == "1"  || "${COLLECTSTATIC}" == "1" ]]; then
    echo "📊 Tailing logs."
    echo
    docker compose \
        -f docker-compose-local.yaml \
        up --abort-on-container-exit
    docker compose down
else
    echo "📊 Tailing logs."
    echo
    docker compose \
        -f docker-compose-local.yaml \
        up
fi
