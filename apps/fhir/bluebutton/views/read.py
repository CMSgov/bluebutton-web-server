import json
import logging
from collections import OrderedDict
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponse, JsonResponse, HttpResponseNotAllowed

from ..opoutcome_utils import (kickout_403,
                               write_session,
                               find_ikey,
                               get_target_url,
                               SESSION_KEY,
                               ERROR_CODE_LIST,
                               strip_format_for_back_end,
                               request_format,
                               add_key_to_fhir_url,
                               fhir_call_type
                               )

from apps.fhir.bluebutton.utils import (request_call,
                                        check_rt_controls,
                                        check_access_interaction_and_resource_type,
                                        get_fhir_id,
                                        masked_id,
                                        build_params,
                                        FhirServerUrl,
                                        get_host_url,
                                        build_output_dict,
                                        post_process_request,
                                        get_default_path,
                                        get_crosswalk,
                                        get_resourcerouter,
                                        build_rewrite_list,
                                        get_response_text)

logger = logging.getLogger('hhs_server.%s' % __name__)

# Attempting to set a timeout for connection and request for longer requests
# eg. Search.


@csrf_exempt
@login_required()
def read(request, resource_type, id, via_oauth=False, *args, **kwargs):
    """
    Read from Remote FHIR Server

    # Example client use in curl:
    # curl  -X GET http://127.0.0.1:8000/fhir/Practitioner/1234
    """

    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

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
                             via_oauth=via_oauth,
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
                 'INTERACTION_TYPE: %s - Via Oauth:%s' % (interaction_type,
                                                          via_oauth))

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

    # TODO: Compare id to cx.fhir_id and return 403 if they don't match for
    # Resource Type - Patient
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
            fhir_url += get_fhir_id(cx) + "/"

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

        # add key to fhir_url unless already in place.
        fhir_url = add_key_to_fhir_url(fhir_url, key)

    logger.debug('FHIR URL with key:%s' % fhir_url)

    ###########################

    # Now we get to process the API Call.

    # Internal handling format is json
    # Remove the oauth elements from the GET

    pass_params = request.GET

    # Let's store the inbound requested format
    # We need to simplify the format call to the backend
    # so that we get data we can manipulate

    # if format is not defined and we come in via_oauth
    # then default to json for format
    requested_format = request_format(pass_params)

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
                id = get_fhir_id(cx).split('/')[1]
            else:
                id = get_fhir_id(cx)
            # logger.debug("Patient Id:%s" % r_id)

    if resource_type.lower() == "patient":
        key = get_fhir_id(cx)
    else:
        key = id

    pass_params = build_params(pass_params,
                               srtc,
                               key,
                               patient_id=get_fhir_id(cx)
                               )

    # Add the call type ( READ = nothing, VREAD, _HISTORY)
    # Before we add an identifier key
    pass_to = fhir_call_type(interaction_type, fhir_url, vid)

    logger.debug('\nHere is the URL to send, %s now add '
                 'GET parameters %s' % (pass_to, pass_params))

    if pass_params is not '':
        pass_to += pass_params

    logger.debug("\nMaking request:%s" % pass_to)

    # Now make the call to the backend API

    if interaction_type == "search":
        r = request_call(request,
                         pass_to,
                         cx,
                         reverse_lazy('home'),
                         timeout=rr.wait_time)
    else:
        r = request_call(request, pass_to, cx, reverse_lazy('home'))

    # BACK FROM THE CALL TO BACKEND

    # Check for Error here
    logger.debug("status: %s/%s" % (r.status_code, r._status_code))

    if r.status_code in ERROR_CODE_LIST:
        logger.debug("We have an error code to deal with: %s" % r.status_code)
        return HttpResponse(json.dumps(r._content, indent=4),
                            status=r.status_code,
                            content_type='application/json')

    text_out = ''
    host_path = get_host_url(request, resource_type)[:-1]
    # logger.debug('host path:%s' % host_path)

    # Add default FHIR Server URL to re-write
    rewrite_url_list = build_rewrite_list(cx)

    text_in = get_response_text(fhir_response=r)

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
    except Exception:
        ikey = ''

    if ikey is not '':
        save_url = get_target_url(fhir_url, resource_type)
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
        return HttpResponse(r.text,
                            content_type='application/xml')

    return JsonResponse(od['bundle'])
