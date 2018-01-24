import logging
from urllib.parse import urlencode
from django.http import JsonResponse, HttpResponseNotAllowed

from ..opoutcome_utils import (kickout_403,
                               kickout_502,
                               strip_format_for_back_end,
                               add_key_to_fhir_url,
                               fhir_call_type)

from apps.fhir.bluebutton.utils import (request_call,
                                        check_rt_controls,
                                        check_access_interaction_and_resource_type,
                                        get_fhir_id,
                                        masked_id,
                                        FhirServerUrl,
                                        get_host_url,
                                        post_process_request,
                                        get_default_path,
                                        get_crosswalk,
                                        get_resourcerouter,
                                        build_rewrite_list,
                                        get_response_text)

from apps.dot_ext.decorators import capability_protected_resource

logger = logging.getLogger('hhs_server.%s' % __name__)


@capability_protected_resource()
def oauth_read(request, resource_type, id, via_oauth=True, *args, **kwargs):
    """
    Read from Remote FHIR Server
    # Example client use in curl:
    # curl  -X GET http://127.0.0.1:8000/fhir/Practitioner/1234
    """

    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    interaction_type = 'read'

    return generic_read(request,
                        interaction_type,
                        resource_type,
                        id,
                        via_oauth,
                        *args,
                        **kwargs)


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
        fhir_url = default_path + resource_type + '/'

        if srtc.override_url_id:
            fhir_url += get_fhir_id(cx) + "/"
        else:
            fhir_url += id + "/"

    else:
        logger.debug('CX:%s' % cx)
        if cx:
            fhir_url = cx.get_fhir_resource_url(resource_type)
        else:
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

    # now we simplify the format/_format request for the back-end
    pass_params = strip_format_for_back_end(pass_params)

    # #### SEARCH

    if interaction_type == 'search':
        if cx is not None:
            if cx.fhir_id.__contains__('/'):
                id = get_fhir_id(cx).split('/')[1]
            else:
                id = get_fhir_id(cx)

    key = get_fhir_id(cx) if resource_type.lower() == "patient" else id

    pass_params = urlencode(pass_params)

    # Add the call type ( READ = nothing, VREAD, _HISTORY)
    # Before we add an identifier key
    pass_to = fhir_call_type(interaction_type, fhir_url, vid)

    logger.debug('\nHere is the URL to send, %s now add '
                 'GET parameters %s' % (pass_to, pass_params))

    if pass_params:
        pass_to += '?' + pass_params

    timeout = rr.wait_time if interaction_type == "search" else None

    logger.debug("\nMaking request:%s" % pass_to)

    # Now make the call to the backend API

    r = request_call(request, pass_to, cx, timeout=timeout)

    # BACK FROM THE CALL TO BACKEND

    # Check for Error here
    logger.debug("status: %s/%s" % (r.status_code, r._status_code))

    if r.status_code >= 300:
        return kickout_502('An error occurred contacting the upstream server')

    host_path = get_host_url(request, resource_type)[:-1]

    # Add default FHIR Server URL to re-write
    rewrite_url_list = build_rewrite_list(cx)

    text_in = get_response_text(fhir_response=r)

    text_out = post_process_request(request,
                                    host_path,
                                    text_in,
                                    rewrite_url_list)

    return JsonResponse(text_out)
