#!/usr/bin/env bash

./check-env-preconditions.bash

echo "Launching the stack. Woosh."


if [ "${ENV}" = "local" ]; then
    PROFILE="mock-sls"
elif [ "${ENV}" = "test" ]; then
    PROFILE="slsx"
elif [ "${ENV}" = "sbx" ]; then
    PROFILE="slsx"
else
    echo "ENV must be set to 'test' or 'sbx'."
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
        echo "I think things are still running. Bringing the stack down."
        TAKE_IT_DOWN="YES"
    fi
done

if [ "${TAKE_IT_DOWN}" = "YES" ]; then
    for id in $DOCKER_PS; do
        echo "Stopping container $id"
        docker stop $id
    done
fi

echo "Vernier start."

docker compose \
    --profile slsx \
    -f docker-compose-local.yaml \
    up