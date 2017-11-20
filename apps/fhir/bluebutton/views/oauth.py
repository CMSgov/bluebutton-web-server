#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server/apps/fhir/bluebutton/views/
FILE: oauth.py
Created: 8/28/17 3:10 PM

File created by: '@ekivemark'
Based on code written by Alan Viars in TransparentHealth/django-monfhir
"""

from __future__ import absolute_import
from __future__ import unicode_literals
from django.http import HttpResponse

from .read import oauth_read
from ..opoutcome_utils import kickout_400
from apps.dot_ext.decorators import capability_protected_resource


@capability_protected_resource()
def oauth_read_or_update_or_delete(request, resource_type, id):
    """Route to read, update, or delete based on HTTP method FHIR Interaction"""

    if request.method == 'GET':
        # Read
        return oauth_read(request, resource_type, id, via_oauth=True)
    # elif request.method == 'PUT':
    #     # update
    #     return update(request, resource_type, id, via_oauth=True)
    # elif request.method == 'DELETE':
    #     # delete
    #     return delete(request, resource_type, id, via_oauth=True)
    # else:
    # Not supported.
    msg = "HTTP method %s not supported at this URL." % (request.method)
    return kickout_400(msg)


@capability_protected_resource()
def oauth_view(request, resource_type):
    if request.method == "GET":
        return oauth_read(request, resource_type, via_oauth=True)
    return HttpResponse(status=501)
