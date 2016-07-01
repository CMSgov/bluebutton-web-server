#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: apps.eimm.urls
Created: 7/1/16 12:51 PM


"""
from django.conf.urls import url
from django.contrib import admin

from .views import connect_first

__author__ = 'Mark Scrimshire:@ekivemark'

admin.autodiscover()

urlpatterns = [
    # URLs with login_required protection

    # Conformance statement
    url(r'mymedicare-connect$',
        connect_first,
        name='eimm_connectfirst'),

]
