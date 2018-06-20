#!/usr/bin/env python
import os
import sys
import dotenv


if __name__ == "__main__":
    if os.environ.get('DJANGO_DOTENV_FILE', None):
        dotenv.read_dotenv(os.environ.get('DJANGO_DOTENV_FILE'))
    else:
        dotenv.read_dotenv()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                          "hhs_oauth_server.settings.base")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
