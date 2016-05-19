#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: apps.fhir.core.utils
Created: 5/19/16 1:02 PM


"""
__author__ = 'Mark Scrimshire:@ekivemark'

import json

from collections import OrderedDict

from django.conf import settings
from django.http import HttpResponse

from apps.fhir.server.models import SupportedResourceType, ResourceTypeControl


def kickout_400(reason, status_code=400):

    oo = OrderedDict()
    oo['resourceType']= "OperationOutcome"
    oo['issue'] = []
    issue = OrderedDict()
    issue['severity']='fatal'
    issue['code']='exception'
    issue['details']= reason
    return HttpResponse(json.dumps(oo, indent = 4),
                        status=status_code,
                        content_type="application/json")


def kickout_401(reason, status_code=401):
    oo = OrderedDict()
    oo['resourceType']= "OperationOutcome"
    oo['issue'] = []
    issue = OrderedDict()
    issue['severity']='fatal'
    issue['code']='security'
    issue['details']= reason
    oo['issue'].append(issue)
    return HttpResponse(json.dumps(oo, indent = 4),
                        status=status_code,
                        content_type="application/json")


def kickout_403(reason, status_code=403):
    oo = OrderedDict()
    oo['resourceType']= "OperationOutcome"
    oo['issue'] = []
    issue = OrderedDict()
    issue['severity']='fatal'
    issue['code']='security'
    issue['details']= reason
    oo['issue'].append(issue)
    return HttpResponse(json.dumps(oo, indent = 4),
                        status=status_code,
                        content_type="application/json")


def kickout_404(reason, status_code=404):
    oo = OrderedDict()
    oo['resourceType']= "OperationOutcome"
    oo['issue'] = []
    issue = OrderedDict()
    issue['severity']='fatal'
    issue['code']='not-found'
    issue['details']= reason
    oo['issue'].append(issue)
    return HttpResponse(json.dumps(oo, indent = 4),
                        status=status_code,
                        content_type="application/json")


def kickout_500(reason, status_code=500):
    oo = OrderedDict()
    oo['resourceType']= "OperationOutcome"
    oo['issue'] = []
    issue = OrderedDict()
    issue['severity']='fatal'
    issue['code']='exception'
    issue['details']= reason
    oo['issue'].append(issue)
    return HttpResponse(json.dumps(oo, indent = 4),
                        status=status_code,
                        content_type="application/json")


def check_access_interaction_and_resource_type(resource_type, interaction_type):
    try:
        rt = SupportedResourceType.objects.get(resource_name=resource_type)
        if interaction_type not in rt.get_supported_interaction_types():
            msg = "The interaction: %s is not permitted on %s FHIR " \
                  "resources on this FHIR sever." % (interaction_type,
                                                     resource_type)
            return kickout_403(msg)
    except SupportedResourceType.DoesNotExist:
        msg = "%s is not a supported resource type on this FHIR server." % resource_type
        return kickout_404(msg)
    return False


def check_rt_controls(resource_type):
    # Check for controls to apply to this resource_type
    if settings.DEBUG:
        print("Resource_Type = ", resource_type)
    rt = SupportedResourceType.objects.get(resource_name=resource_type)
    if settings.DEBUG:
        print("Working with SupportedResourceType:", rt)
    try:
        srtc = ResourceTypeControl.objects.get(resource_name=rt)
    except ResourceTypeControl.DoesNotExist:
        srtc = None

    return srtc