#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: route_rud
Created: 5/23/16 6:29 PM


"""
__author__ = 'Mark Scrimshire:@ekivemark'

from django.shortcuts import render

DF_EXTRA_INFO = False

from apps.fhir.core.utils import kickout_400
# from apps.fhir.bluebutton.views.update import update
# from apps.fhir.bluebutton.views.delete import delete
from apps.fhir.bluebutton.views.read import read

from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def read_or_update_or_delete(request, resource_type, id):
    """Route to read, update, or delete based on HTTP method FHIR Interaction"""

    if request.method == 'GET':
        # Read
        return read(request, resource_type, id)
    # elif request.method == 'PUT':
    #     # update
    #     return update(request, resource_type, id)
    # elif request.method == 'DELETE':
    #     # delete
    #     return delete(request, resource_type, id)
    # else:
    # Not supported.
    msg = "HTTP method %s not supported at this URL." % (request.method)
    return kickout_400(msg)


