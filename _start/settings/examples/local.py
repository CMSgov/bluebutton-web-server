#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: local.py
Created: 5/16/16 12:10 AM


"""
__author__ = 'Mark Scrimshire:@ekivemark'

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

if DEBUG:
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
