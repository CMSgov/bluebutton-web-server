"""
hhs_oauth_server
FILE: context
Created: 8/24/16 1:10 PM

File created by: ''

Create a function that will perform a contextprocessor function and
return a True or False based on whether an app is in settings.INSTALLED_APPS

The purpose is to simplify Environment/Installation Specific code branching

Installation Specific code should be islated to an app that is embedded
in the list of installed apps.
Custom HTML should be installed in the templates/{app_Name} folder inside
the application.

"""
from django.conf import settings


def IsAppInstalled(target_app=None):
    """ Is an app in INSTALLED_APPS """

    if target_app:
        if target_app in settings.INSTALLED_APPS:
            return True
    # Return False if target_app is not defined
    # or target_app is not found in INSTALLED_APPS
    return False


def active_apps(request):
    """ Is app active in INSTALLED_APPS """

    return {'active_apps': settings.INSTALLED_APPS}
