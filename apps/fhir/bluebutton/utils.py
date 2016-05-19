#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: apps.fhir.bluebutton.utils
Created: 5/19/16 12:35 PM


"""
__author__ = 'Mark Scrimshire:@ekivemark'

from apps.fhir.core.utils import (kickout_404, kickout_403)
from apps.fhir.server.models import SupportedResourceType


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

