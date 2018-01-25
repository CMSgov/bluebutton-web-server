from django.http import JsonResponse
import logging
from urllib.parse import urlencode

from ..constants import ALLOWED_RESOURCE_TYPES
from ..decorators import require_valid_token
from ..errors import build_error_response, method_not_allowed

from apps.fhir.bluebutton.utils import (request_call,
                                        get_fhir_id,
                                        get_host_url,
                                        post_process_request,
                                        get_crosswalk,
                                        get_resourcerouter,
                                        build_rewrite_list,
                                        get_response_text)

from ..opoutcome_utils import (kickout_502,
                               strip_format_for_back_end,
                               fhir_call_type)

logger = logging.getLogger('hhs_server.%s' % __name__)


@require_valid_token()
def read(request, resource_type, id, *args, **kwargs):
    """
    Read from Remote FHIR Server
    # Example client use in curl:
    # curl -X GET http://127.0.0.1:8000/fhir/Practitioner/1234
    """

    logger.debug("resource_type: %s" % resource_type)
    logger.debug("Interaction: read. ")
    logger.debug("Request.path: %s" % request.path)

    if request.method != 'GET':
        return method_not_allowed(['GET'])

    if resource_type not in ALLOWED_RESOURCE_TYPES:
        logger.info('User requested read access to the %s resource type' % resource_type)
        return build_error_response(404, 'The requested resource type, %s, is not supported'
                                         % resource_type)

    crosswalk = get_crosswalk(request.resource_owner)

    # If the user isn't matched to a backend ID, they have no permissions
    if crosswalk is None:
        logger.info('Crosswalk for %s does not exist' % request.user)
        return build_error_response(403, 'No access information was found for the authenticated user')

    resource_router = get_resourcerouter(crosswalk)

    if resource_type == 'Patient':
        id = get_fhir_id(crosswalk)

    target_url = resource_router.fhir_url + resource_type + "/" + id + "/"

    logger.debug('FHIR URL with key:%s' % target_url)

    ###########################

    # Now we get to process the API Call.

    # Internal handling format is json
    # Remove the oauth elements from the GET

    pass_params = request.GET

    # now we simplify the format/_format request for the back-end
    pass_params = strip_format_for_back_end(pass_params)

    pass_params = urlencode(pass_params)

    # Add the call type ( READ = nothing, VREAD, _HISTORY)
    # Before we add an identifier key
    pass_to = fhir_call_type('read', target_url)

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

    if r.status_code == 404:
        return build_error_response(404, 'The requested resource does not exist')

    if r.status_code >= 300:
        return kickout_502('An error occurred contacting the upstream server')

    host_path = get_host_url(request, resource_type)[:-1]

    # Add default FHIR Server URL to re-write
    rewrite_url_list = build_rewrite_list(crosswalk)
    text_in = get_response_text(fhir_response=r)
    text_out = post_process_request(request, host_path, text_in, rewrite_url_list)

    return JsonResponse(text_out)
