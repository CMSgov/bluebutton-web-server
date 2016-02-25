#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from views import *


urlpatterns = patterns('',
    #Read -----------------------------------
    url(r'^read/$', api_read, name="api_read"),

    #Write-----------------------------------
    url(r'^write/$', api_write, name="api_write"),
    )
