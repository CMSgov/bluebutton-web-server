#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: wsgi_test.py
Created: 5/16/16 12:10 AM

Use this for testing if the mod_wsgi app is working in the same way as
python manage.py runserver
ideas based on http://blog.dscpl.com.au/2010/03/improved-wsgi-script-for-use-with.html


"""
__author__ = 'Mark Scrimshire:@ekivemark'

import sys
from .base import *
from platform import python_version

DEBUG = True

SECRET_KEY = "BBOAUTH2-LOCAL-_CHANGE_THIS_FAKE_KEY_TO_YOUR_OWN_SECRET_KEY"

# define app managers 
ADMINS = (
    ('Mark Scrimshire', 'mark@ekivemark.com'),
)
MANAGERS = ADMINS

ALLOWED_HOSTS = ['*']

# Suppress printing for dumpdata to avoid polluting dump files
SUPPRESS_PRINT = ['dumpdata',]  # 'runserver'

if DEBUG and not sys.argv[1].lower() in SUPPRESS_PRINT:
    print("==========================================================")
    # APPLICATION_TITLE is set in .base
    print(APPLICATION_TITLE)
    # SETTINGS_MODE should be set in base to DJANGO_SETTINGS_MODULE
    print("Mode:", SETTINGS_MODE)
    print("running on", python_version())
    # We should add note to base.py to make sure
    # ADMINS and MANAGERS are set in the custom settings file
    print("Application Managers:", MANAGERS)
    print("==========================================================")
