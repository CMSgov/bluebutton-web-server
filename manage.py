#!/usr/bin/env python
import os
import sys

DJANGO_CUSTOM_SETTINGS_DIR = os.environ.get("DJANGO_CUSTOM_SETTINGS_DIR", '..')
EXEC_FILE = os.path.join(DJANGO_CUSTOM_SETTINGS_DIR, 'custom-envvars.py')

# check if custom-envvars.py exists
# If it does then run it
if os.path.isfile(EXEC_FILE):

    # Python2
    try:
        execfile(EXEC_FILE)             # NOQA
    except NameError:
        # Python3 - execfile call format changed
        exec(open(EXEC_FILE).read())

else:
    print("no custom variables set:[%s] - Not Found" % EXEC_FILE)

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                          "hhs_oauth_server.settings.base")

    # print("DATABASES_CUSTOM=%s" % os.environ.get('DATABASES_CUSTOM'))
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
