#!/usr/bin/env bash

set -e
set -a


# Bounce localhost:9090 inside the container to s3mock:9090
# This is necessary to start early for collectstatic.
echo "🔵 running socat localhost:9090 -> docker.internal:9090"
socat TCP-LISTEN:9090,fork,reuseaddr TCP:host.docker.internal:9090 &

# We exit the stack if we're running migrations
# or collecting static files. These are run-and-quit
# actions. They have their own make targets locally.
if [ "${MIGRATE}" = "1" ]
then
    echo "🔵 running migrate"
    python manage.py migrate
    echo "🔵 done running migrate ; bring down the stack"
    exit 0
fi

if [ "${COLLECTSTATIC}" = "1" ]
then    
    echo "🔵 running collectstatic"
    python manage.py collectstatic --noinput
    echo "🔵 done running collectstatic; bring down the stack"
    exit 0
fi


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

if [ "${UNIT_TEST_NAME}" != "" ];
then
    echo "🐛⏯️ Start bluebutton server with remote debugging and wait attach for a single test..."
    python3 -m debugpy --listen 0.0.0.0:5678 --wait-for-client runtests.py ${UNIT_TEST_NAME}
    exit
fi

if [ "${BB20_ENABLE_REMOTE_DEBUG}" = true ];
then
    if [ "${BB20_REMOTE_DEBUG_WAIT_ATTACH}" = true ];
    then
        echo "🐛⏯️ Start bluebutton server with remote debugging and wait attach..."
        python3 -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m gunicorn hhs_oauth_server.wsgi:application --worker-tmp-dir /dev/shm --bind 0.0.0.0:8000 --workers 4 --timeout 120 --reload
    else
        echo "🐛 Start bluebutton server with debugging, no waiting"
        python3 -m debugpy --listen 0.0.0.0:5678 -m gunicorn hhs_oauth_server.wsgi:application --worker-tmp-dir /dev/shm --bind 0.0.0.0:8000 --workers 4 --timeout 120 --reload
    fi
else
        echo "🔵 Start bluebutton server"
        gunicorn hhs_oauth_server.wsgi:application --worker-tmp-dir /dev/shm --bind 0.0.0.0:8000 --workers 4 --timeout 120 --reload --log-level debug
fi