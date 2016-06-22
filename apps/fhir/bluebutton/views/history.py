#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: history
Created: 5/23/16 6:37 PM


"""
__author__ = 'Mark Scrimshire:@ekivemark'

import logging

from apps.fhir.bluebutton.views.read import generic_read

logger = logging.getLogger('hhs_server.%s' % __name__)

DF_EXTRA_INFO = False


def history(request, resource_type, id, *args, **kwargs):
    """
    Read from Remote FHIR Server

    # Example client use in curl:
    # curl  -X GET http://127.0.0.1:8000/fhir/Practitioner/1234
    """

    interaction_type = '_history'

    history = generic_read(request, interaction_type, resource_type, id, *args, **kwargs)

    return history


