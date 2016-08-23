#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: apps.extapi.urls
Created: 8/23/16 8:34 AM

File created by: 'Mark Scrimshire' @ekivemark
"""
from django.conf.urls import url
from django.views.generic import TemplateView

# Add Site specific html pages here.
# Use format: TemplateView.as_view(template_name='{name}')

urlpatterns = [
    # url(r'^intro_step1/$', intro_step1.as_view()),
    url(r'^intro_step1/$', TemplateView.as_view(template_name='extapi/intro_step1.html')),
]