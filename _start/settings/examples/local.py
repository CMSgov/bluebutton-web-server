from .base import *
from platform import python_version

DEBUG = True

SECRET_KEY = "BBOAUTH2-LOCAL-_CHANGE_THIS_FAKE_KEY_TO_YOUR_OWN_SECRET_KEY"

if DEBUG:
    print("Managers:", MANAGERS)
    
# define app managers 
ADMINS = (
    ('Mark Scrimshire', 'mark@ekivemark.com'),
)


if DEBUG:
    print("==========================================================")
    # APPLICATION_TITLE is set in .base
    print(APPLICATION_TITLE)
    print("running on", python_version())
    # checking if MANAGERS gets updated or do we needed to 
    # update MANAGERS too
    # in which case we should add note to base.py to make sure
    # these are set in the custom settings file
    print("Application Managers:", MANAGERS)
    print("==========================================================")
