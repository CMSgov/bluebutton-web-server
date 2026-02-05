#!/usr/bin/env bash

set -e
set -a


# Bounce localhost:9090 inside the container to s3mock:9090
# This is necessary to start early for collectstatic.
echo "🔵 running socat localhost:9090 -> docker.internal:9090"
socat TCP-LISTEN:9090,fork,reuseaddr TCP:host.docker.internal:9090 &

if [ "${DB_MIGRATIONS}" = "true" ]
then

    echo "🔵 running migrations"
    python manage.py migrate

    # echo "🔵 running collectstatic"
    # python manage.py collectstatic --noinput >/dev/null 2>&1

    # We will recrate this with every launch.
    # echo "TRUNCATE authorization_archiveddataaccessgrant;" | psql "${DATABASES_CUSTOM}"

    # Only create the root user if it doesn't exist.
    result=$(python manage.py shell --verbosity 0 -c "from django.contrib.auth.models import User; print(1) if User.objects.filter(username='${SUPER_USER_NAME}').exists() else print(0)")
    if [[ "$result" == "0" ]]; then
        echo "from django.contrib.auth.models import User; User.objects.create_superuser('${SUPER_USER_NAME}', '${SUPER_USER_EMAIL}', '${SUPER_USER_PASSWORD}')" | python manage.py shell
        echo "🆗 created ${SUPER_USER_NAME} user."
    else
        echo "🆗 ${SUPER_USER_NAME} already exists."
    fi


    python manage.py create_test_feature_switches
    echo "🆗 create_test_feature_switches"
    
    python manage.py create_admin_groups
    echo "🆗 create_admin_groups"
    
    python manage.py create_blue_button_scopes
    echo "🆗 create_blue_button_scopes"

    python manage.py create_test_user_and_application

    echo "🆗 create_test_user_and_application"

    python manage.py create_user_identification_label_selection
    echo "🆗 create_user_identification_label_selection"

else
    echo "restarting blue button server, no db image migration and models initialization will run here, you might need to manually run DB image migrations."
fi

if [ "${TEST}" != "" ];
then
    echo "🐛⏯️ Start bluebutton server with remote debugging and wait attach for a single test..."
    python3 -m debugpy --listen 0.0.0.0:5678 --wait-for-client runtests.py ${TEST}
    exit
fi

if [ "${BB20_ENABLE_REMOTE_DEBUG}" = true ];
then
    if [ "${BB20_REMOTE_DEBUG_WAIT_ATTACH}" = true ];
    then
        echo "🐛⏯️ Start bluebutton server with remote debugging and wait attach..."
        python3 -m debugpy --listen 0.0.0.0:5678 --wait-for-client manage.py runserver 0.0.0.0:8000
    else
        echo "🐛 Start bluebutton server with debugging, no waiting"
        python3 -m debugpy --listen 0.0.0.0:5678 manage.py runserver 0.0.0.0:8000 ${TEST}
    fi
else
        echo "🔵 Start bluebutton server"
        python3 manage.py runserver 0.0.0.0:8000
fi