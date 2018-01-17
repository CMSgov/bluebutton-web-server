# Environment Settings

Always import from base into any settings file you create.

    from .base import *
    
base.py is the master settings file.

Django enables a new settings file to be loaded by using the Environment
Variable:
    
    DJANGO_SETTINGS_MODULE
    
by default wsgi.py sets this variable to:

    "hhs_oauth_server.settings.base"
    
To point to an environment specific file change DJANGO_SETTINGS_MODULE to

    "hhs_oauth_server.settings.{new_environment_file_wothout_py_extension}"
    
eg.

    "hhs_oauth_server.settings.aws-test"
    
The bluebutton-web-deplyoment scripts deploy environment-specific settings
files for each CMS Environment.

