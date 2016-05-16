from .base import *

DEBUG = True

SECRET_KEY = "BBOAUTH2-LOCAL-_CHANGE_THIS_FAKE_KEY_TO_YOUR_OWN_SECRET_KEY"

# define app managers
ADMINS = (
    ('Mark Scrimshire', 'mark@ekivemark.com'),
)
MANAGERS = ADMINS

ALLOWED_HOSTS = ['*']

if DEBUG:
    print("==========================================================")
    # APPLICATION_TITLE is set in .base
    print(APPLICATION_TITLE)
    # SETTINGS_MODE should be set in base to DJANGO_SETTINGS_MODULE
    print("Mode:", SETTINGS_MODE)
    print("running on", python_version())
    # checking if MANAGERS gets updated or do we needed to
    # update MANAGERS too
    # in which case we should add note to base.py to make sure
    # these are set in the custom settings file
    print("Application Managers:", MANAGERS)
    print("==========================================================")
