from django.http import JsonResponse, HttpResponseNotAllowed
import logging
from urllib.parse import urlencode

from apps.dot_ext.decorators import require_valid_token

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

from ..opoutcome_utils import (kickout_403,
                               kickout_502,
                               strip_format_for_back_end,
                               add_key_to_fhir_url,
                               fhir_call_type)

logger = logging.getLogger('hhs_server.%s' % __name__)


@require_valid_token()
def read(request, resource_type, id, *args, **kwargs):
    """
    Read from Remote FHIR Server
    # Example client use in curl:
    # curl  -X GET http://127.0.0.1:8000/fhir/Practitioner/1234
    """

    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    logger.debug("resource_type: %s" % resource_type)
    logger.debug("Interaction: read. ")
    logger.debug("Request.path: %s" % request.path)

    crosswalk = get_crosswalk(request.resource_owner)

    resource_router = get_resourcerouter(crosswalk)

    # Check if this interaction type and resource type combo is allowed.
    deny = check_access_interaction_and_resource_type(resource_type, 'read', resource_router)

    if deny:
        return deny

    supported_resource_type_control = check_rt_controls(resource_type, resource_router)

    if crosswalk is None:
        logger.debug('Crosswalk for %s does not exist' % request.user)

    if (crosswalk is None and supported_resource_type_control is not None):
        if supported_resource_type_control.override_search:
            # If user is not in Crosswalk and supported_resource_type_control has search_override = True
            # We need to prevent search to avoid data leakage.
            return kickout_403('Error 403: %s Resource is access controlled.'
                               ' No records are linked to user:'
                               '%s' % (resource_type, request.user))

    fhir_url = ''
    # change source of default_url to ResourceRouter

    default_path = get_default_path(supported_resource_type_control.resource_name, cx=crosswalk)
    # get the default path for resource with ending "/"
    # You need to add resource_type + "/" for full url

    if supported_resource_type_control:
        fhir_url = default_path + resource_type + '/'

        if supported_resource_type_control.override_url_id:
            fhir_url += get_fhir_id(crosswalk) + "/"
        else:
            fhir_url += id + "/"

    else:
        logger.debug('Crosswalk: %s' % crosswalk)
        if crosswalk:
            fhir_url = crosswalk.get_fhir_resource_url(resource_type)
        else:
            fhir_url = FhirServerUrl() + resource_type + '/'

    key = masked_id(resource_type, crosswalk, supported_resource_type_control, id, slash=False)

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

    key = get_fhir_id(crosswalk) if resource_type.lower() == "patient" else id

    pass_params = urlencode(pass_params)

    # Add the call type ( READ = nothing, VREAD, _HISTORY)
    # Before we add an identifier key
    pass_to = fhir_call_type('read', fhir_url)

    logger.debug('Here is the URL to send, %s now add '
                 'GET parameters %s' % (pass_to, pass_params))

    if pass_params:
        pass_to += '?' + pass_params

    timeout = None

    logger.debug("Making request:%s" % pass_to)

    # Now make the call to the backend API

    r = request_call(request, pass_to, crosswalk, timeout=timeout)

    # Check for Error here
    logger.debug("status: %s/%s" % (r.status_code, r._status_code))

    if r.status_code >= 300:
        return kickout_502('An error occurred contacting the upstream server')

    host_path = get_host_url(request, resource_type)[:-1]

    # Add default FHIR Server URL to re-write
    rewrite_url_list = build_rewrite_list(crosswalk)

    text_in = get_response_text(fhir_response=r)

    text_out = post_process_request(request,
                                    host_path,
                                    text_in,
                                    rewrite_url_list)

    return JsonResponse(text_out)
