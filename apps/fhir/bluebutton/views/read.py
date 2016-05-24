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

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render

from apps.fhir.core.utils import (check_access_interaction_and_resource_type,
                                  check_rt_controls)

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

    # interaction_type = 'read' or '_history' or 'vread'
    if settings.DEBUG:
        print("interaction_type:", interaction_type)
    #Check if this interaction type and resource type combo is allowed.
    deny = check_access_interaction_and_resource_type(resource_type, interaction_type)
    if deny:
        #If not allowed, return a 4xx error.
        return deny

    srtc = check_rt_controls(resource_type)
    # We get back an Supported ResourceType Control record or None

    if settings.DEBUG:
        if srtc:
            print("Parameter Restrictions:", srtc.parameter_restriction())
        else:
            print("No Resource Controls found")

        print("Working with id:", id)

    key = id
    if srtc:
        if srtc.force_url_id_override:
            key = crosswalk_id(request, id)
            if key == None:
                if not id == None:
                    key = id

            # Crosswalk returns the new id or returns None
            if settings.DEBUG:
                print("crosswalk:", key, ":", request.user)
        else:
            # No Id_Overide so use the original id
            key = id
    else:
        key = id

    # Do we have a key?
    # if key == None:
    #     return kickout_404("FHIR_IO_HAPI:Search needs a valid Resource Id that is linked "
    #                        "to the authenticated user "
    #                        "(%s) which was not available" % request.user)

    # Now we get to process the API Call.

    if settings.DEBUG:
        print("Now we need to evaluate the parameters and arguments"
              " to work with ", key, "and ", request.user)
        print("GET Parameters:", request.GET, ":")

    mask = False
    if srtc:
        if srtc.force_url_id_override:
            mask = True

    in_fmt = "json"
    Txn = {'name': resource_type,
           'display': resource_type,
           'mask': mask,
           'in_fmt': in_fmt,
           }

    skip_parm = []
    if srtc:
        skip_parm = srtc.parameter_restriction()

    #skip_parm = ['_id',
    #             'access_token', 'client_id', 'response_type', 'state']

    if settings.DEBUG:
        print('Masking the following parameters', skip_parm)
    # access_token can be passed in as a part of OAuth protected request.
    # as can: state=random_state_string&response_type=code&client_id=ABCDEF
    # Remove it before passing url through to FHIR Server

    pass_params = build_params(request.GET, skip_parm)
    if settings.DEBUG:
        print("Parameters:", pass_params)

    if interaction_type == "vread":
        pass_to = FhirServerUrl() + "/"+ resource_type  + "/" + key + "/" + "_history" + "/" + vid
    elif interaction_type == "_history":
        pass_to = FhirServerUrl() + "/" + resource_type + "/" + key + "/" + "_history"
    else:  # interaction_type == "read":
        pass_to = FhirServerUrl() + "/" + resource_type + "/" + key + "/"

    print("Here is the URL to send, %s now get parameters %s" % (pass_to,pass_params))

    if pass_params != "":
        pass_to += pass_params

    # Now make the call to the backend API
    try:
        r = requests.get(pass_to)

    except requests.ConnectionError:
        if settings.DEBUG:
            print("Problem connecting to FHIR Server")
        messages.error(request, "FHIR Server is unreachable." )
        return HttpResponseRedirect(reverse_lazy('api:v1:home'))

    if r.status_code in [301, 302, 400, 403, 404, 500]:
        return error_status(r, r.status_code)

    text_out = ""
    if settings.DEBUG:
        print("r:", r.text)

    if '_format=xml' in pass_params:
        text_out= minidom.parseString(r.text).toprettyxml()
    else:
        text_out = r.json()

    od = OrderedDict()
    if DF_EXTRA_INFO:
        od['request_method']= request.method
        od['interaction_type'] = interaction_type
    od['resource_type']    = resource_type
    od['id'] = key
    if vid != None:
        od['vid'] = vid

    if settings.DEBUG:
        print("Query List:", request.META['QUERY_STRING'] )

    if DF_EXTRA_INFO:
        od['parameters'] = request.GET.urlencode()
        if settings.DEBUG:
            print("or:", od['parameters'])

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
        od['note'] = 'This is the %s Pass Thru (%s) ' % (resource_type,key)
        if settings.DEBUG:
            od['note'] += 'using: %s ' % (pass_to)
            print(od)

    if fmt == "xml":
        if settings.DEBUG:
            print("We got xml back in od")
        return HttpResponse( tostring(dict_to_xml('content', od)),
                             content_type="application/%s" % fmt)
    elif fmt == "json":
        if settings.DEBUG:
            print("We got json back in od")
        return HttpResponse(json.dumps(od, indent=4),
                            content_type="application/%s" % fmt)

    if settings.DEBUG:
        print("We got a different format:%s" % fmt)
    return render(request,
                  'fhir_io_hapi/default.html',
                  {'content': json.dumps(od, indent=4),
                   'output': od},
                  )
