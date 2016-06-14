#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: apps
Created: 6/14/16 5:47 PM


"""
__author__ = 'Mark Scrimshire:@ekivemark'

from django.apps import AppConfig

class dot_extConfig(AppConfig):
    name = 'apps.dot_ext'
    label = 'dot_ext'
    verbose_name = "Django Oauth Toolkit Extension"
