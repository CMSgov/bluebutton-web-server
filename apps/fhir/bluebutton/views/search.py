import json

import logging

from collections import OrderedDict

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from apps.dot_ext.decorators import capability_protected_resource

from ..opoutcome_utils import (find_ikey,
                               get_target_url,
                               ERROR_CODE_LIST,
                               kickout_400,
                               kickout_403,
                               kickout_404,
                               request_format,
                               SESSION_KEY,
                               write_session)

from apps.fhir.bluebutton.utils import (request_get_with_parms,
                                        block_params,
                                        build_output_dict,
                                        build_rewrite_list,
                                        check_access_interaction_and_resource_type,
                                        check_rt_controls,
                                        get_crosswalk,
                                        get_fhir_id,
                                        get_host_url,
                                        get_resourcerouter,
                                        post_process_request,
                                        pretty_json,
                                        get_response_text)

from apps.fhir.bluebutton.views.home import (fhir_conformance,
                                             fhir_search_home)

from apps.fhir.server.utils import (set_fhir_format,
                                    set_resource_id,
                                    search_add_to_list,
                                    payload_additions,
                                    payload_var_replace)

logger = logging.getLogger('hhs_server.%s' % __name__)
logger_error = logging.getLogger('hhs_server_error.%s' % __name__)
logger_debug = logging.getLogger('hhs_server_debug.%s' % __name__)
logger_info = logging.getLogger('hhs_server_info.%s' % __name__)

DF_EXTRA_INFO = False


@csrf_exempt
def search_simple(request, resource_type, via_oauth=False, *args, **kwargs):
    """Route to search FHIR Interaction"""

    if request.method == 'GET':
        # Search
        logger.debug("searching with Resource:"
                     "%s and Id:%s" % (resource_type, id))

        return read_search(request, resource_type, id, via_oauth)

    # elif request.method == 'PUT':
    #     # update
    #     return update(request, resource_type, id, via_oauth)
    # elif request.method == 'DELETE':
    #     # delete
    #     return delete(request, resource_type, id, via_oauth)
    # else:
    # Not supported.
    msg = "HTTP method %s not supported at this URL." % (request.method)
    # logger_info.info(msg)
    logger.debug(msg)

    return kickout_400(msg)


@login_required()
def search(request, resource_type, *args, **kwargs):
    """
    Search from Remote FHIR Server

    # Example client use in curl:
    # curl  -X GET http://127.0.0.1:8000/fhir/Practitioner/
    """

    interaction_type = 'search'

    logger.debug("Received:%s" % resource_type)
    logger_debug.debug("Received:%s" % resource_type)

    conformance = False
    if "_getpages" in request.GET:
        # a request can be made without a resource name
        # if the GET Parameters include _getpages it is asking for the
        # next batch of resources from a previous search
        conformance = False
        logger.debug("We need to get a searchset: %s" % request.GET)

    elif resource_type is None:
        conformance = True
    elif resource_type.lower() == 'metadata':
        # metadata is a valid resourceType to request the
        # Conformance/Capability Statement
        conformance = True
    elif resource_type.lower == 'conformance':
        # Conformance is the Dstu2 name for the list of resources supported
        conformance = True
    elif resource_type.lower == "capability":
        # Capability is the Stu3 name for the list of resources supported
        conformance = True

    if conformance:
        return fhir_conformance(request, resource_type, *args, **kwargs)

    logger.debug("Interaction:%s. "
                 "Calling generic_read for %s" % (interaction_type,
                                                  resource_type))

    logger_debug.debug("Interaction:%s. "
                       "Calling generic_read for %s" % (interaction_type,
                                                        resource_type))

    if "_getpages" in request.GET:
        # Handle the next searchset
        search = fhir_search_home(request, via_oauth=False)

    else:
        # Otherwise we should have a resource_type and can perform a search
        search = read_search(request,
                             interaction_type,
                             resource_type,
                             # rt_id=None,
                             via_oauth=False,
                             *args,
                             **kwargs)
    return search


@capability_protected_resource()
def oauth_search(request, resource_type, *args, **kwargs):
    """
    Search from Remote FHIR Server

    # Example client use in curl:
    # curl  -X GET http://127.0.0.1:8000/fhir/Practitioner/
    """

    interaction_type = 'search'

    logger.debug("Received:%s" % resource_type)
    logger_debug.debug("Received:%s" % resource_type)

    conformance = False
    if "_getpages" in request.GET:
        # a request can be made without a resource name
        # if the GET Parameters include _getpages it is asking for the
        # next batch of resources from a previous search
        conformance = False
        logger.debug("We need to get a searchset: %s" % request.GET)

    elif resource_type is None:
        conformance = True
    elif resource_type.lower() == 'metadata':
        # metadata is a valid resourceType to request the
        # Conformance/Capability Statement
        conformance = True
    elif resource_type.lower == 'conformance':
        # Conformance is the Dstu2 name for the list of resources supported
        conformance = True
    elif resource_type.lower == "capability":
        # Capability is the Stu3 name for the list of resources supported
        conformance = True
    elif resource_type.lower == "capabilitystatement":
        # Capability is the Stu3 name for the list of resources supported
        conformance = True

    if conformance:
        return fhir_conformance(request, resource_type, *args, **kwargs)

    logger.debug("Interaction:%s. "
                 "Calling generic_read for %s" % (interaction_type,
                                                  resource_type))

    logger_debug.debug("Interaction:%s. "
                       "Calling generic_read for %s" % (interaction_type,
                                                        resource_type))

    if "_getpages" in request.GET:
        # Handle the next searchset
        search = fhir_search_home(request, via_oauth=True)
    else:
        # Otherwise we should have a resource_type and can perform a search
        search = read_search(request,
                             interaction_type,
                             resource_type,
                             # rt_id=None,
                             via_oauth=True,
                             *args,
                             **kwargs)
    return search


def read_search(request,
                interaction_type,
                resource_type,
                via_oauth=False,
                id=None,
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
    # curl  -X GET http://127.0.0.1:8000/fhir/Practitioner/1234?_format=json


    """

    logger.debug('\n========================\n'
                 'INTERACTION_TYPE: %s - via OAuth:%s' % (interaction_type,
                                                          via_oauth))
    logger.debug("Request.path:%s" % request.path)

    # Get the users crosswalk
    if via_oauth:
        cx = get_crosswalk(request.resource_owner)
    else:
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

    if srtc is None:
        return kickout_404('Unsupported ResourceType')

    if not via_oauth:
        if srtc.secure_access and request.user.is_anonymous():
            return kickout_403('Error 403: %s Resource access is controlled.'
                               ' Login is required:'
                               '%s' % (resource_type, request.user.is_anonymous()))
            # logger.debug('srtc: %s' % srtc)

    if (cx is None and srtc is not None):
        # There is a srtc record so we need to check override_search
        if srtc.override_search:
            # If user is not in Crosswalk and srtc has search_override = True
            # We need to prevent search to avoid data leakage.
            return kickout_403('Error 403: %s Resource is access controlled.'
                               ' No records are linked to user:'
                               '%s' % (resource_type, request.user))

    ################################################
    #
    # Now we should have sorted out all the bounces
    # Now to structure the call to the back-end
    #
    ################################################

    # construct the server address, path and release
    # Get the crosswalk.fhir_source = ResourceRouter

    # Build url from rr.server_address + rr.server_path + rr.server_release

    target_url = rr.fhir_url

    # add resource_type + '/'
    target_url += srtc.resourceType

    target_url += "/"

    # Analyze the _format parameter
    # Sve the display _format

    input_parameters = request.GET
    requested_format = request_format(input_parameters)

    # prepare the back-end _format setting
    back_end_format = set_fhir_format(requested_format)

    # request.GET is immutable so take a copy to allow the values to be edited.
    payload = request.GET.copy()

    # Get payload with oauth parameters removed
    # Add the format for back-end
    payload['_format'] = back_end_format

    # remove the srtc.search_block parameters
    payload = block_params(payload, srtc)

    # move resource_id to _id=resource_id
    id_dict = set_resource_id(srtc, id, get_fhir_id(cx))

    # Add the srtc.search_add parameters
    params_list = search_add_to_list(srtc.search_add)

    payload = payload_additions(payload, params_list)

    if id_dict['_id']:
        # add rt_id into the search parameters
        if id_dict['_id'] is not None:
            payload['_id'] = id_dict['_id']

    if resource_type.lower() == 'patient':
        logger.debug("Working resource:%s" % resource_type)
        logger.debug("Working payload:%s" % payload)
        logger.debug("id_dict:%s" % id_dict)

        payload['_id'] = id_dict['patient']
        if 'patient' in payload:
            del payload['patient']

    for pyld_k, pyld_v in payload.items():
        if pyld_v is None:
            pass
        elif '%PATIENT%' in pyld_v:
            # replace %PATIENT% with cx.fhir_id

            payload = payload_var_replace(payload,
                                          pyld_k,
                                          new_value=id_dict['patient'],
                                          old_value='%PATIENT%')

    # add the _format setting
    payload['_format'] = back_end_format

    ###############################################
    ###############################################
    # Make the request_call
    r = request_get_with_parms(request,
                               target_url,
                               json.loads(json.dumps(payload)),
                               cx,
                               reverse_lazy('home'),
                               timeout=rr.wait_time
                               )

    ###############################################
    ###############################################
    #
    # Now we process the response from the back-end
    #
    ################################################

    if r.status_code in ERROR_CODE_LIST:
        logger.debug("We have an error code to deal with: %s" % r.status_code)
        return HttpResponse(json.dumps(r._content, indent=4),
                            status=r.status_code,
                            content_type='application/json')

    rewrite_list = build_rewrite_list(cx)
    host_path = get_host_url(request, resource_type)[:-1]

    text_in = get_response_text(fhir_response=r)

    text_out = post_process_request(request,
                                    back_end_format,
                                    host_path,
                                    text_in,
                                    rewrite_list)

    if resource_type.lower() == 'patient':
        display_key = id_dict['patient']
    else:
        display_key = id
    od = build_output_dict(request,
                           OrderedDict(),
                           resource_type,
                           display_key,
                           vid,
                           interaction_type,
                           requested_format,
                           text_out)

    ################################################
    #
    # Now display the result
    #
    ################################################
    ikey = ''
    try:
        ikey = find_ikey(r.text)
    except Exception:
        ikey = ''

    if ikey is not '':

        save_url = get_target_url(target_url, resource_type)
        content = {
            'fhir_to': save_url,
            'rwrt_list': rewrite_list,
            'res_type': resource_type,
            'intn_type': interaction_type,
            'key': display_key,
            'vid': vid,
            'resource_router': rr.id
        }
        sesn_var = write_session(request, ikey, content, skey=SESSION_KEY)
        if sesn_var:
            logger.debug("Problem writing session variables."
                         " Returned %s" % sesn_var)

    if requested_format == 'xml':
        return HttpResponse(r.text, content_type='application/xml')

    return HttpResponse(pretty_json(od['bundle']),
                        content_type='application/json')
