#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
apps.fhir.testac
FILE: urls
Created: 7/26/16 1:43 PM

File created by: Mark Scrimshire @ekivemark
"""

from django.conf.urls import url
from django.contrib import admin

from .views import check_crosswalk

admin.autodiscover()

urlpatterns = [
    # Upload a BlueButton Text File
    # check Crosswalk before giving access to upload
    url(r'bb_upload/',
        check_crosswalk,
        name='bb_upload'),
]
