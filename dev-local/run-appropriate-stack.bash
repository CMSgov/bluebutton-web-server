#!/usr/bin/env bash
source ./check-pre-post.bash
source ./retrieve-certs-and-salt.bash

# this says to "export all variables."
set -a
# exit on error.
set -e


######################################################################
# let's make sure we have a valid ENV var before proceeding
check_valid_env

######################################################################
# source the baseline environment variables
# these set the stage for all further environment manipulation for 
# launching the app.
source ./.env.local

# add another check or two after we source the env file.
check_env_after_source

######################################################################
# let's make sure the .env.local sourced in correctly.
check_env_preconditions

# set the FHIR_URL and FHIR_URL_V3
set_fhir_urls

# set the profile for docker compose
set_profile

# retrieve the certs and store them in $HOME/.bb2/certstore
retrieve_certs

set_salt

echo "🚀 Launching the stack for '${ENV}'."

echo "FHIR_URLs are:"
echo "  * ${FHIR_URL}"
echo "  * ${FHIR_URL_V3}"

DOCKER_PS=$(docker ps -q)
echo $DOCKER_PS

TAKE_IT_DOWN="NO"
for id in $DOCKER_PS; do
    NAME=$(docker inspect --format '{{.Config.Image}}' $id)
    if [[ "${NAME}" =~ "postgres" ]]; then
        echo "🤔 I think things are still running. Bringing the stack down."
        TAKE_IT_DOWN="YES"
    fi
done

if [ "${TAKE_IT_DOWN}" = "YES" ]; then
    for id in $DOCKER_PS; do
        echo "🛑 Stopping container $id"
        docker stop $id
    done
fi

echo "📊 Vernier start."
echo

docker compose \
    --profile "${PROFILE}" \
    -f docker-compose-local.yaml \
    up