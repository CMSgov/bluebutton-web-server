#!/usr/bin/env bash

./check-env-preconditions.bash

echo "🚀 Launching the stack."


if [ "${ENV}" = "local" ]; then
    PROFILE="mock-sls"
elif [ "${ENV}" = "test" ]; then
    PROFILE="slsx"
    export FHIR_URL="${FHIR_URL_TEST}"
    export FHIR_URL_V3="${FHIR_URL_V3_TEST}"
elif [ "${ENV}" = "sbx" ]; then
    PROFILE="slsx"
    export FHIR_URL="${FHIR_URL_SBX}"
    export FHIR_URL_V3="${FHIR_URL_V3_SBX}"
else
    echo "ENV must be set to 'local', 'test', or 'sbx'."
    echo "ENV is currently set to '${ENV}'."
    echo "Exiting."
    exit -2
fi

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
    --profile slsx \
    -f docker-compose-local.yaml \
    up