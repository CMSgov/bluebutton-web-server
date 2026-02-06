#!/usr/bin/env python
import os
import sys
# replace django dotenv (latest release is 2017) with python dotenv
from dotenv import load_dotenv


if __name__ == "__main__":
    if os.getenv('DJANGO_DOTENV_FILE', None):
        load_dotenv(os.getenv('DJANGO_DOTENV_FILE'))
    else:
        load_dotenv()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                          "hhs_oauth_server.settings.base")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
