# CUSTOM SETTINGS

To implement a custom settings file for your environment:

1. Copy an example from the _start.settings.examples folder
2. edit the file with your own settings and sensitive key values
3. Set DJANGO_SETTINGS_MODULE

in linux this is done as follows, using _start.settings.local.py as the example

    export DJANGO_SETTINGS_MODULE=_start.settings.local

then run: 

    python manage.py runserver 8000

Do not store the custom settings files in the git repository.
