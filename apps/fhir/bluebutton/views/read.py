import json
import logging

from collections import OrderedDict

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponse
from django.shortcuts import render

from apps.fhir.fhir_core.utils import (kickout_403,
                                       write_session,
                                       find_ikey,
                                       # get_search_param_format,
                                       get_target_url,
                                       # content_is_json_or_xml,
                                       # get_content_type,
                                       SESSION_KEY,
                                       # error_status,
                                       ERROR_CODE_LIST,
                                       build_querystring,
                                       strip_format_for_back_end,
                                       request_format,
                                       add_key_to_fhir_url,
                                       fhir_call_type,
                                       get_div_from_json
                                       )

from apps.fhir.bluebutton.utils import (request_call,
                                        check_rt_controls,
                                        check_access_interaction_and_resource_type,
                                        masked_id,
                                        strip_oauth,
                                        build_params,
                                        FhirServerUrl,
                                        get_host_url,
                                        build_output_dict,
                                        post_process_request,
                                        pretty_json,
                                        get_default_path,
                                        get_crosswalk,
                                        get_resourcerouter,
                                        build_rewrite_list)

# from apps.fhir.bluebutton.views.search import read_search

from apps.fhir.bluebutton.xml_handler import get_div_from_xml

# moved Crosswalk access to bluebutton.utils.get_crosswalk
# from apps.fhir.bluebutton.models import Crosswalk

logger = logging.getLogger('hhs_server.%s' % __name__)
# logger_error = logging.getLogger('hhs_server_error.%s' % __name__)
# logger_debug = logging.getLogger('hhs_server_debug.%s' % __name__)
# logger_info = logging.getLogger('hhs_server_info.%s' % __name__)

# Attempting to set a timeout for connection and request for longer requests
# eg. Search.


@login_required()
def read(request, resource_type, id, via_oauth=False, *args, **kwargs):
    """
    Read from Remote FHIR Server

    # Example client use in curl:
    # curl  -X GET http://127.0.0.1:8000/fhir/Practitioner/1234
    """

    interaction_type = 'read'

    read_fhir = generic_read(request,
                             interaction_type,
                             resource_type,
                             id,
                             via_oauth,
                             *args,
                             **kwargs)

    return read_fhir


def oauth_read(request, resource_type, id, via_oauth, *args, **kwargs):
    """
    Read from Remote FHIR Server
    Called from oauth.py

    # Example client use in curl:
    # curl  -X GET http://127.0.0.1:8000/fhir/Practitioner/1234
    """

    interaction_type = 'read'

    read_fhir = generic_read(request,
                             interaction_type,
                             resource_type,
                             id,
                             via_oauth,
                             *args,
                             **kwargs)

    return read_fhir


def generic_read(request,
                 interaction_type,
                 resource_type,
                 id=None,
                 via_oauth=False,
                 vid=None,
                 *args,
                 **kwargs):
    """
    Read from remote FHIR Server

    :param request:
    :param interaction_type:
    :param resource_type:
    :param id:
    :param vid:
    :param args:
    :param kwargs:
    :return:

    # Example client use in curl:
    # curl  -X GET http://127.0.0.1:8000/fhir/Practitioner/1234

    Process flow:

    Is it a valid request?

    Get the target server info

    Get the request modifiers
    - change url_id
    - remove unwanted search parameters
    - add search parameters

    Construct the call

    Make the call

    Check result for errors

    Deliver the formatted result


    """
    # DONE: Fix to allow url_id in url for non-key resources.
    # eg. Patient is key resource so replace url if override_url_id is True
    # if override_url_id is not set allow id to be applied and check
    # if search_override is True.
    # interaction_type = 'read' or '_history' or 'vread' or 'search'
    logger.debug('\n========================\n'
                 'INTERACTION_TYPE: %s' % interaction_type)

    # if via_oauth we need to call crosswalk with
    if via_oauth:
        # get crosswalk from the resource_owner
        cx = get_crosswalk(request.resource_owner)
    else:
        # Get the users crosswalk
        cx = get_crosswalk(request.user)

    # cx will be the crosswalk record or None
    rr = get_resourcerouter(cx)

    # Check if this interaction type and resource type combo is allowed.
    deny = check_access_interaction_and_resource_type(resource_type,
                                                      interaction_type,
                                                      rr)
    if deny:
        # if not allowed, return a 4xx error.
        return deny

    srtc = check_rt_controls(resource_type, rr)
    # We get back a Supported ResourceType Control record or None
    # with earlier if deny step we should have a valid srtc.

    if not via_oauth:
        # we don't need to check if user is anonymous if coming via_oauth
        if srtc.secure_access and request.user.is_anonymous():
            return kickout_403('Error 403: %s Resource access is controlled.'
                               ' Login is required:'
                               '%s' % (resource_type,
                                       request.user.is_anonymous()))
        # logger.debug('srtc: %s' % srtc)

    if cx is None:
        logger.debug('Crosswalk for %s does not exist' % request.user)

    if (cx is None and srtc is not None):
        # There is a srtc record so we need to check override_search
        if srtc.override_search:
            # If user is not in Crosswalk and srtc has search_override = True
            # We need to prevent search to avoid data leakage.
            return kickout_403('Error 403: %s Resource is access controlled.'
                               ' No records are linked to user:'
                               '%s' % (resource_type, request.user))

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

    fhir_url = ''
    # change source of default_url to ResourceRouter

    default_path = get_default_path(srtc.resource_name,
                                    cx=cx)
    # get the default path for resource with ending "/"
    # You need to add resource_type + "/" for full url

    if srtc:
        # logger.debug('SRTC:%s' % srtc)

        fhir_url = default_path + resource_type + '/'

        if srtc.override_url_id:
            fhir_url += cx.fhir_id + "/"

        # logger.debug('fhir_url:%s' % fhir_url)
        else:
            fhir_url += id + "/"

    else:
        logger.debug('CX:%s' % cx)
        if cx:
            fhir_url = cx.get_fhir_resource_url(resource_type)
        else:
            # logger.debug('FHIRServer:%s' % FhirServerUrl())
            fhir_url = FhirServerUrl() + resource_type + '/'

    # #### SEARCH

    if interaction_type == 'search':
        key = None
    else:
        key = masked_id(resource_type, cx, srtc, id, slash=False)

        # print("\nMasked_id-key:%s from r_id:%s "
        #       "and cx-fhir_id:%s\n" % (key, id, cx.fhir_id))

        # add key to fhir_url unless already in place.
        fhir_url = add_key_to_fhir_url(fhir_url, key)

    logger.debug('FHIR URL with key:%s' % fhir_url)

    ###########################

    # Now we get to process the API Call.

    # Internal handling format is json
    # Remove the oauth elements from the GET
    pass_params = strip_oauth(request.GET)

    # Let's store the inbound requested format
    # We need to simplify the format call to the backend
    # so that we get data we can manipulate

    # if format is not defined and we come in via_oauth
    # then default to json for format
    requested_format = request_format(pass_params)
    if requested_format == "html" and via_oauth:
        requested_format = "json"

    # now we simplify the format/_format request for the back-end
    pass_params = strip_format_for_back_end(pass_params)
    if "_format" in pass_params:
        back_end_format = pass_params['_format']
    else:
        back_end_format = "json"

    # #### SEARCH

    if interaction_type == 'search':
        if cx is not None:
            # logger.debug("cx.fhir_id=%s" % cx.fhir_id)
            if cx.fhir_id.__contains__('/'):
                id = cx.fhir_id.split('/')[1]
            else:
                id = cx.fhir_id
            # logger.debug("Patient Id:%s" % r_id)

    if resource_type.lower() == "patient":
        key = cx.fhir_id
    else:
        key = id

    pass_params = build_params(pass_params,
                               srtc,
                               key,
                               patient_id=cx.fhir_id
                               )

    # Add the call type ( READ = nothing, VREAD, _HISTORY)
    # Before we add an identifier key
    pass_to = fhir_call_type(interaction_type, fhir_url, vid)

    logger.debug('\nHere is the URL to send, %s now add '
                 'GET parameters %s' % (pass_to, pass_params))

    if pass_params is not '':
        pass_to += pass_params

    logger.debug("\nMaking request:%s" % pass_to)
    query_string = build_querystring(request.GET.copy())

    ###############################################
    ###############################################
    # Now make the call to the backend API

    if interaction_type == "search":
        r = request_call(request,
                         pass_to,
                         cx,
                         reverse_lazy('home'),
                         timeout=settings.REQUEST_CALL_TIMEOUT)
    else:
        r = request_call(request, pass_to, cx, reverse_lazy('home'))

    # BACK FROM THE CALL TO BACKEND
    ###############################################
    ###############################################

    # logger.debug("r returned: %s" % r)

    # Check for Error here
    logger.debug("what is in r:\n#######\n%s\n##########\n" % dir(r))
    logger.debug("status: %s/%s" % (r.status_code, r._status_code))
    # logger.debug("text: %s\n#############\n" % (r.text))

    if r.status_code in ERROR_CODE_LIST:
        logger.debug("We have an error code to deal with: %s" % r.status_code)
        if 'html' in requested_format.lower():
            return render(
                request,
                'bluebutton/default.html',
                {'output': pretty_json(r._content, indent=4),
                 'fhir_id': cx.fhir_id,
                 'content': {'parameters': query_string,
                             'resource_type': resource_type,
                             'id': id,
                             'request_method': "GET",
                             'interaction_type': interaction_type,
                             'div_texts': "",
                             'source': cx.fhir_source.name}})
        else:
            return HttpResponse(json.dumps(r._content, indent=4),
                                status=r.status_code,
                                content_type='application/json')

        # return error_status(r, r.status_code, r._text)

    # try:
    #     error_check = r.text
    #     # logger.debug("We got r.text back:%s" % r.text[:200] + "...")
    # except:
    #     error_check = "HttpResponse status_code=502"
    #     logger.debug("Something went wrong with call to %s" % pass_to)
    # logger.debug("Checking for errors:%s" % error_check[:200] + "...")
    # if 'status_code' in error_check:
    #     # logger.debug("We have a status code to check: %s" % r)
    #     if r.status_code in ERROR_CODE_LIST:
    #         logger.debug("\nError Status Code:%s" % r.status_code)
    #         return error_status(r, r.status_code)
    # elif 'status_code=302' in error_check:
    #     return error_status(r, 302)
    # elif 'status_code=502' in error_check:
    #     return error_status(r, 502)
    # else:
    #     logger.debug("Status Code:%s "
    #                  "in:%s" % (r.status_code, r))
    #
    # # We should have a 200 - good record to deal with
    # # We can occasionally get a 200 with a Connection Error. eg. Timeout
    # try:
    #     if "ConnectionError" in r.text:
    #         logger.debug("Error:%s" % r.text)
    #         return error_status(r, 502)
    # except:
    #     pass

    text_out = ''
    # if 'text' in r:
    #     logger.debug('r:%s' % r.text)
    #     logger_debug.debug('r:%s' % r.text)
    # else:
    #     logger.debug("r not returning text:%s" % r)
    #     logger_debug.debug("r not returning text:%s" % r)
    #     logger.debug("r.json: %s" % json.dumps(r.json))

    # logger.debug('Rewrite List:%s' % rewrite_url_list)

    host_path = get_host_url(request, resource_type)[:-1]
    # logger.debug('host path:%s' % host_path)

    # Add default FHIR Server URL to re-write
    rewrite_url_list = build_rewrite_list(cx)
    # print("Starting Rewrite_list:%s" % rewrite_url_list)

    # ct_detail = get_content_type(r)
    # logger.debug('Content-Type:%s \n work with %s' % (ct_detail,
    #                                                   back_end_format))

    try:
        text_in = r.text
    except:
        text_in = ""

    text_out = post_process_request(request,
                                    back_end_format,
                                    host_path,
                                    text_in,
                                    rewrite_url_list)

    od = build_output_dict(request,
                           OrderedDict(),
                           resource_type,
                           key,
                           vid,
                           interaction_type,
                           requested_format,
                           text_out)

    # write session variables if _getpages was found
    ikey = ''
    try:
        ikey = find_ikey(r.text)
    except:
        ikey = ''

    if ikey is not '':

        save_url = get_target_url(fhir_url, resource_type)
        # print("Store fhir_url:%s but only: %s" % (fhir_url,save_url))
        content = {
            'fhir_to': save_url,
            'rwrt_list': rewrite_url_list,
            'res_type': resource_type,
            'intn_type': interaction_type,
            'key': key,
            'vid': vid,
            'resource_router': rr.id
        }
        sesn_var = write_session(request, ikey, content, skey=SESSION_KEY)
        if sesn_var:
            logger.debug("Problem writing session variables."
                         " Returned %s" % sesn_var)
    if requested_format == 'xml':
        # logger.debug('We got xml back in od')
        return HttpResponse(r.text,
                            content_type='application/%s' % requested_format)
        # return HttpResponse(tostring(dict_to_xml('content', od)),
        #                     content_type='application/%s' % requested_format)

    elif requested_format == 'json':
        # logger.debug('We got json back in od')
        return HttpResponse(pretty_json(od['bundle']),
                            content_type='application/%s' % requested_format)

    # define query string further up before request_call
    # query_string = build_querystring(request.GET.copy())
    if "xml" in requested_format:
        # logger.debug("Sending text_out for display: %s" % text_out[0:100])
        div_text = get_div_from_xml(text_out)
        # print("DIV TEXT returned:[%s]%s" % (type(div_text), div_text))
        return render(
            request,
            'bluebutton/default_xml.html',
            {'output': text_out,
             'fhir_id': cx.fhir_id,
             'content': {'parameters': query_string,
                         'resource_type': resource_type,
                         'id': id,
                         'request_method': "GET",
                         'interaction_type': interaction_type,
                         'div_texts': [div_text, ],
                         'source': cx.fhir_source.name}})

    else:
        text_out = pretty_json(od['bundle'])
        div_text = get_div_from_json(od['bundle'])

    # logger.debug('We got a different format:%s' % requested_format)
    logger.debug('id or key: %s/%s' % (id, key))

    return render(
        request,
        'bluebutton/default.html',
        {'output': text_out,
         'fhir_id': cx.fhir_id,
         'content': {'parameters': query_string,
                     'resource_type': resource_type,
                     'id': id,
                     'request_method': "GET",
                     'interaction_type': interaction_type,
                     'div_texts': div_text,
                     'source': cx.fhir_source.name}})
