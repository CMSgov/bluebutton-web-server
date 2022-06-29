#!/usr/bin/env python
import os
import sys
from dotenv import load_dotenv
import logging

logger = logging.getLogger("bb2_entry_point")

logger.error("Hey Django got executed................................")

if __name__ == "__main__":
    logger.error("Hey Django got executed................................ about to load env")
    if os.environ.get('DJANGO_DOTENV_FILE', None):
        # dotenv.read_dotenv(os.environ.get('DJANGO_DOTENV_FILE'))
        load_dotenv(os.environ.get('DJANGO_DOTENV_FILE'))
        logger.error("Hey Django got executed................................ load env {}".format(os.environ.get('DJANGO_DOTENV_FILE')))
    else:
        # dotenv.read_dotenv()
        load_dotenv()
        logger.error("Hey Django got executed................................ load env from default env (.env)")

    os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                          "hhs_oauth_server.settings.base")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
