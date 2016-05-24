#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: read
Created: 5/19/16 12:38 PM


"""
__author__ = 'Mark Scrimshire:@ekivemark'

import json
import logging
import requests

from collections import OrderedDict

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render

from apps.fhir.bluebutton.utils import (build_params,
                                        FhirServerUrl)
from apps.fhir.core.utils import (error_status)

from apps.fhir.bluebutton.utils import (check_access_interaction_and_resource_type,
                                        check_rt_controls,
                                        masked,
                                        masked_id,
                                        strip_oauth)

from apps.fhir.bluebutton.models import Crosswalk


logger = logging.getLogger('hhs_server.%s' % __name__)

DF_EXTRA_INFO = False


def read(request, resource_type, id, *args, **kwargs):
    """
    Read from Remote FHIR Server

    # Example client use in curl:
    # curl  -X GET http://127.0.0.1:8000/fhir/Practitioner/1234
    """

    interaction_type = 'read'

    read = generic_read(request, interaction_type, resource_type, id, *args, **kwargs)

    return read


def generic_read(request, interaction_type, resource_type, id, vid=None, *args, **kwargs):
    """
    Read from remote FHIR Server
    :param resourcetype:
    :param id:
    :return:

    # Example client use in curl:
    # curl  -X GET http://127.0.0.1:8000/fhir/Practitioner/1234

    """
    # quick patch to get request.GET for testing
    print("request.GET:\n", request.GET)

    # interaction_type = 'read' or '_history' or 'vread'
    logger.debug("interaction_type: %s" % interaction_type)

    #Check if this interaction type and resource type combo is allowed.
    deny = check_access_interaction_and_resource_type(resource_type, interaction_type)
    if deny:
        # if not allowed, return a 4xx error.
        return deny

    srtc = check_rt_controls(resource_type)
    # We get back a Supported ResourceType Control record or None

    logger.debug("srtc:%s" % srtc)

    try:
        cx = Crosswalk.objects.get(user=request.user)
    except Crosswalk.DoesNotExist:
        cx = None

    # Request.user = user
    # interaction_type = read | _history | vread
    # resource_type = 'Patient | Practitioner | ExplanationOfBenefit ...'
    # id = fhir_id (potentially masked)
    # vid = Version Id

    # Check the resource_type to see if it has a url
    # Check the resource_type to see if masking is required
    # Get the FHIR_Server (from crosswalk via request.user)
    # if masked get the fhir_id from crosswalk
    # if search_override strip search items (search_block)
    # if search_override add search keys

    fhir_url = ""
    # get the default_url from ResourceTypeControl
    if srtc:
        logger.debug('SRTC:%s' % srtc)
        if srtc.default_url == "":
            fhir_url = FhirServerUrl() + resource_type + "/"
        else:
            fhir_url = srtc.default_url + resource_type + "/"
    else:
        logger.debug('CX:%s' % cx)
        if cx:
            fhir_url = cx.get_fhir_resource_url(resource_type)
        else:
            logger.debug('FHIRServer:%s' % FhirServerUrl())
            fhir_url = FhirServerUrl() + resource_type + "/"

    logger.debug("FHIR URL:%s" % fhir_url)

    key = masked_id(cx, srtc, resource_type, id, slash=False)
    fhir_url += key + "/"

    ####

    # Now we get to process the API Call.

    logger.debug("Now we need to evaluate the parameters and arguments"
                 " to work with %s and %s. GET parameters:%s" % (key, request.user, request.GET))

    mask = masked(srtc)
    # Internal handling format is json
    in_fmt = "json"

    Txn = {'name': resource_type,
           'display': resource_type,
           'mask': mask,
           'in_fmt': in_fmt,
           }

    # Remove the oauth elements from the GET
    pass_params = strip_oauth(request.GET)

    pass_params = build_params(pass_params, srtc, id)

    if interaction_type == "vread":
        pass_to = fhir_url + "_history" + "/" + vid
    elif interaction_type == "_history":
        pass_to = fhir_url + "/" + "_history"
    else:  # interaction_type == "read":
        pass_to = fhir_url

    logger.debug("Here is the URL to send, %s now add GET parameters %s" % (pass_to,pass_params))

    if pass_params != "":
        pass_to += pass_params

    # Now make the call to the backend API
    try:
        r = requests.get(pass_to)

    except requests.ConnectionError:
        logger.debug("Problem connecting to FHIR Server")
        messages.error(request, "FHIR Server is unreachable." )
        return HttpResponseRedirect(reverse_lazy('api:v1:home'))

    if r.status_code in [301, 302, 400, 401, 402, 403, 404, 500, 501, 502, 503, 504]:
        return error_status(r, r.status_code)

    text_out = ""
    logger.debug("r:%s" % r.text)

    if '_format=xml' in pass_params.lower():
        # We will add xml support later
        pass

        text_out = r.text
        # text_out= minidom.parseString(r.text).toprettyxml()
    else:
        # dealing with json
        text_out = r.json()

    od = OrderedDict()
    if DF_EXTRA_INFO:
        od['request_method']= request.method
        od['interaction_type'] = interaction_type
    od['resource_type']    = resource_type
    od['id'] = key
    if vid != None:
        od['vid'] = vid

    logger.debug("Query List:%s" % request.META['QUERY_STRING'] )

    if DF_EXTRA_INFO:
        od['parameters'] = request.GET.urlencode()
        logger.debug("or:%s" % od['parameters'])

    if '_format=xml' in pass_params.lower():
        fmt = "xml"
    elif '_format=json' in pass_params.lower():
        fmt = "json"
    else:
        fmt = ''

    if DF_EXTRA_INFO:
        od['format'] = fmt
    od['bundle'] = text_out

    if DF_EXTRA_INFO:
        od['note'] = 'This is the %s Pass Thru (%s) ' % (resource_type, key)
        if settings.DEBUG:
            od['note'] += 'using: %s ' % (pass_to)
            print(od)

    if fmt == "xml":
        logger.debug("We got xml back in od")
        return HttpResponse(r.text, content_type="application/%s" % fmt )
        # return HttpResponse( tostring(dict_to_xml('content', od)),
        #                      content_type="application/%s" % fmt)
    elif fmt == "json":
        logger.debug("We got json back in od")
        return HttpResponse(json.dumps(od, indent=4),
                            content_type="application/%s" % fmt)

    logger.debug("We got a different format:%s" % fmt)
    return render(request,
                  'fhir_io_hapi/default.html',
                  {'content': json.dumps(od, indent=4),
                   'output': od},
                  )
