#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: urls
Created: 10/19/16 4:17 PM

File created by: 'Mark Scrimshire @ekivemark'
"""
from django.conf.urls import url
from django.contrib import admin
from django.views.generic import TemplateView

admin.autodiscover()

urlpatterns = [
    url(r'^agreement/1/$',
        TemplateView.as_view(template_name='agreement_1.html'),
        name='learn_0'),
    url(r'^policy/1/$',
        TemplateView.as_view(template_name='policy_1.html'),
        name='learn_0'),
]
