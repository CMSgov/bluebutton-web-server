#!/bin/sh

DB_MIGRATIONS=${DB_MIGRATIONS:-true}
SUPER_USER_NAME=${SUPER_USER_NAME:-'root'}
SUPER_USER_EMAIL=${SUPER_USER_EMAIL:-'bluebutton@example.com'}
SUPER_USER_PASSWORD=${SUPER_USER_PASSWORD:-'bluebutton123'}
BB20_ENABLE_REMOTE_DEBUG=${BB20_ENABLE_REMOTE_DEBUG:-false}
BB20_REMOTE_DEBUG_WAIT_ATTACH=${BB20_REMOTE_DEBUG_WAIT_ATTACH:-false}

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

if [ "${BB20_ENABLE_PROFILING}" = false ]
then
    if [ "${BB20_ENABLE_REMOTE_DEBUG}" = true ]
    then
        if [ "${BB20_REMOTE_DEBUG_WAIT_ATTACH}" = true ]
        then
            echo "Start bluebutton server with remote debugging and wait attach..."
            python3 -m debugpy --listen 0.0.0.0:5678 --wait-for-client manage.py runserver 0.0.0.0:8000 --noreload
        else
            echo "Start bluebutton server with remote debugging..."
            python3 -m debugpy --listen 0.0.0.0:5678 manage.py runserver 0.0.0.0:8000 --noreload
        fi
    else
        echo "Start bluebutton server ..."
        python3 manage.py runserver 0.0.0.0:8000
    fi
else
    echo "Start bluebutton server with runprofileserver ..."
    if [ -d 'bb2_profile_stats' ]
    then
        rm -rf bb2_profile_stats
    fi
    mkdir bb2_profile_stats
    # python3 manage.py runserver 0.0.0.0:8000
    python3 manage.py runprofileserver --kcachegrind --use-cprofile --prof-path=/code/bb2_profile_stats 0.0.0.0:8000
fi
