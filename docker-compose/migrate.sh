#!/bin/sh

python manage.py migrate

python manage.py createsuperuser
python manage.py create_admin_groups
python manage.py create_blue_button_scopes
python manage.py setup_bluebutton
python manage.py create_test_user_and_application
