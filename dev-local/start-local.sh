#!/usr/bin/env bash

set -a

if [ "${DB_MIGRATIONS}" = "true" ]
then
    echo "🆗 running migrations"
    python manage.py migrate

    # We will recrate this with every launch.
    # echo "TRUNCATE authorization_archiveddataaccessgrant;" | psql "${DATABASES_CUSTOM}"

    # Only create the root user if it doesn't exist.
    result=$(echo "from django.contrib.auth.models import User; print(1) if User.objects.filter(username='${SUPER_USER_NAME}').exists() else print(0)" | python manage.py shell)
    if [[ "$result" == "0" ]]; then
        echo "🆗 creating ${} user."
        echo "from django.contrib.auth.models import User; User.objects.create_superuser('${SUPER_USER_NAME}', '${SUPER_USER_EMAIL}', '${SUPER_USER_PASSWORD}')" | python manage.py shell
    else
        echo "🆗 ${SUPER_USER_NAME} already exists."
    fi
    
    python manage.py create_admin_groups
    echo "🆗 loading scopes.json"
    python manage.py loaddata scopes.json
    
    python manage.py create_blue_button_scopes
    python manage.py create_test_user_and_application
    python manage.py create_user_identification_label_selection
    echo "creating feature switches......"
    python manage.py create_test_feature_switches
else
    echo "restarting blue button server, no db image migration and models initialization will run here, you might need to manually run DB image migrations."
fi

if [ ! -d 'bluebutton-css' ]
then
    git clone https://github.com/CMSgov/bluebutton-css.git
else
    echo 'CSS already installed.'
fi

if [ "${BB20_ENABLE_REMOTE_DEBUG}" = true ]
then
    if [ "${BB20_REMOTE_DEBUG_WAIT_ATTACH}" = true ]
    then
        if [ "${BB2_SERVER_STD2FILE}" = "YES" ]
        then
            echo "Start bluebutton server with remote debugging and wait attach..., std redirect to file: ${BB2_SERVER_STD2FILE}"
            python3 -m debugpy --listen 0.0.0.0:5678 --wait-for-client manage.py runserver 0.0.0.0:8000 > ./docker-compose/tmp/bb2_email_to_stdout.log 2>&1
        else
            echo "Start bluebutton server with remote debugging and wait attach..."
            # NOTE: The "--noreload" option can be added below to disable if needed
            python3 -m debugpy --listen 0.0.0.0:5678 --wait-for-client manage.py runserver 0.0.0.0:8000
        fi
    else
        if [ "${BB2_SERVER_STD2FILE}" = "YES" ]
        then
            echo "Start bluebutton server with remote debugging..., std redirect to file: ${BB2_SERVER_STD2FILE}"
            python3 -m debugpy --listen 0.0.0.0:5678 manage.py runserver 0.0.0.0:8000 > ./docker-compose/tmp/bb2_email_to_stdout.log 2>&1
        else
            echo "Start bluebutton server with remote debugging..."
            python3 -m debugpy --listen 0.0.0.0:5678 manage.py runserver 0.0.0.0:8000
        fi
    fi
else
    if [ "${BB2_SERVER_STD2FILE}" = "YES" ]
    then
        echo "Start bluebutton server ..., std redirect to file: ${BB2_SERVER_STD2FILE}"
        python3 manage.py runserver 0.0.0.0:8000 > ./docker-compose/tmp/bb2_email_to_stdout.log 2>&1
    else
        echo "Start bluebutton server ..."
        python3 manage.py runserver 0.0.0.0:8000
    fi
fi
