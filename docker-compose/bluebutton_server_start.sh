#!/bin/sh

DB_MIGRATIONS=${DB_MIGRATIONS:-true}
SUPER_USER_NAME=${SUPER_USER_NAME:-'root'}
SUPER_USER_EMAIL=${SUPER_USER_EMAIL:-'bluebutton@example.com'}
SUPER_USER_PASSWORD=${SUPER_USER_PASSWORD:-'bluebutton123'}
BB20_ENABLE_REMOTE_DEBUG=${BB20_ENABLE_REMOTE_DEBUG:-false}
BB20_REMOTE_DEBUG_WAIT_ATTACH=${BB20_REMOTE_DEBUG_WAIT_ATTACH:-false}
BB2_SERVER_STD2FILE=${BB2_SERVER_STD2FILE:-''}

DJANGO_LOG_JSON_FORMAT_PRETTY=${DJANGO_LOG_JSON_FORMAT_PRETTY:-True}
DJANGO_USER_ID_SALT=${DJANGO_USER_ID_SALT:-"6E6F747468657265616C706570706572"}
DJANGO_USER_ID_ITERATIONS=${DJANGO_USER_ID_ITERATIONS:-"2"}

if [ "${DJANGO_SLSX_CLIENT_SECRET}" = "xxxxx" ]
then
    # for msls
    echo "MSLS used for identity service..."
else
    echo "SLSX used for identity service..."
    DJANGO_MEDICARE_SLSX_REDIRECT_URI=${DJANGO_MEDICARE_SLSX_REDIRECT_URI:-"http://localhost:8000/mymedicare/sls-callback"}
    DJANGO_MEDICARE_SLSX_REDIRECT_URI_V1=${DJANGO_MEDICARE_SLSX_REDIRECT_URI_v1:-"http://localhost:8000/mymedicare/sls-callback/v1"}
    DJANGO_MEDICARE_SLSX_LOGIN_URI=${DJANGO_MEDICARE_SLSX_LOGIN_URI:-"https://test.medicare.gov/sso/authorize?client_id=bb2api"}
    DJANGO_SLSX_HEALTH_CHECK_ENDPOINT=${DJANGO_SLSX_HEALTH_CHECK_ENDPOINT:-"https://test.accounts.cms.gov/health"}
    DJANGO_SLSX_TOKEN_ENDPOINT=${DJANGO_SLSX_TOKEN_ENDPOINT:-"https://test.medicare.gov/sso/session"}
    DJANGO_SLSX_SIGNOUT_ENDPOINT=${DJANGO_SLSX_SIGNOUT_ENDPOINT:-"https://test.medicare.gov/sso/signout"}
    DJANGO_SLSX_USERINFO_ENDPOINT=${DJANGO_SLSX_USERINFO_ENDPOINT:-"https://test.accounts.cms.gov/v1/users"}
fi

if [ "${DB_MIGRATIONS}" = true ]
then
    echo "run db image migration and models initialization."
    python manage.py migrate

    echo "from django.contrib.auth.models import User; User.objects.create_superuser('${SUPER_USER_NAME}', '${SUPER_USER_EMAIL}', '${SUPER_USER_PASSWORD}')" | python manage.py shell
    python manage.py create_admin_groups
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
