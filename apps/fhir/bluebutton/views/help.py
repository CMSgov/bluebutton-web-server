#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: help
Created: 9/29/16 5:45 PM

File created by: 'Mark Scrimshire @ekivemark'
"""
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

from ...server.models import SupportedResourceType


def bluebutton_help(request):
    """
    Get Supported Resource Types and display resources
    :param request:
    :return:
    """
    name = _('Blue Button API Help')
    try:
        rt = SupportedResourceType.objects.all()

    except SupportedResourceType.DoesNotExist:
        rt = {}

    # this is a GET
    context = {'name': name,
               'resources': rt}
    template = 'bluebutton-help.html'
    return render(request, template, context)
