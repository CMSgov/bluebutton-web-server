#!/bin/sh

python manage.py migrate
python manage.py loaddata apps/accounts/fixtures/groups.json
python manage.py loaddata apps/accounts/fixtures/scopes.json

python manage.py createsuperuser
python manage.py create_admin_groups
python manage.py create_blue_button_scopes
python manage.py setup_bluebutton
python manage.py collectstatic
