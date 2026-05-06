#!/usr/bin/env python
import os
import sys

from dotenv import load_dotenv

if __name__ == '__main__':
    load_dotenv()

    # this conditional loads the test setting if you are running the test runner
    # this is so that it doesn't load the watchtower logging and make useless log groups
    # and spam them with logs. This should be worked on in the future.
    TESTING = 'test' in sys.argv
    if TESTING:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hhs_oauth_server.settings.test')
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hhs_oauth_server.settings.base')

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
