from django.http import HttpResponse, JsonResponse
import json
import logging

from ..constants import ALLOWED_RESOURCE_TYPES
from ..decorators import require_valid_token
from ..errors import build_error_response

from apps.fhir.bluebutton.utils import (request_get_with_parms,
                                        build_rewrite_list,
                                        get_crosswalk,
                                        get_host_url,
                                        get_resourcerouter,
                                        post_process_request,
                                        get_response_text)

from rest_framework.decorators import throttle_classes, api_view
from apps.dot_ext.throttling import TokenRateThrottle


logger = logging.getLogger('hhs_server.%s' % __name__)


@require_valid_token()
@api_view(['GET'])
@throttle_classes([TokenRateThrottle])
def search(request, resource_type, *args, **kwargs):
    """
    Search from Remote FHIR Server
    """

    logger.debug("resource_type: %s" % resource_type)
    logger.debug("Interaction: search. ")
    logger.debug("Request.path: %s" % request.path)

    if resource_type not in ALLOWED_RESOURCE_TYPES:
        logger.info('User requested search access to the %s resource type' % resource_type)
        return build_error_response(404, 'The requested resource type, %s, is not supported'
                                         % resource_type)

    crosswalk = get_crosswalk(request.resource_owner)

    # If the user isn't matched to a backend ID, they have no permissions
    if crosswalk is None:
        logger.info('Crosswalk for %s does not exist' % request.user)
        return build_error_response(403, 'No access information was found for the authenticated user')

    resource_router = get_resourcerouter(crosswalk)
    target_url = resource_router.fhir_url + resource_type + "/"

    get_parameters = {
        '_format': 'application/json+fhir'
    }

    patient_id = '' if resource_type == 'Patient' else crosswalk.fhir_id

    if 'patient' in request.GET and request.GET['patient'] != patient_id:
        return build_error_response(403, 'You do not have permission to access the requested patient\'s data')

    if resource_type == 'ExplanationOfBenefit':
        get_parameters['patient'] = patient_id
    elif resource_type == 'Coverage':
        get_parameters['beneficiary'] = 'Patient/' + patient_id
        if 'beneficiary' in request.GET and patient_id not in request.GET['beneficiary']:
            return build_error_response(403, 'You do not have permission to access the requested patient\'s data')
    elif resource_type == 'Patient':
        get_parameters['_id'] = ''

    r = request_get_with_parms(request,
                               target_url,
                               get_parameters,
                               crosswalk,
                               timeout=resource_router.wait_time)

    if r.status_code >= 300:
        logger.debug("We have an error code to deal with: %s" % r.status_code)
        return HttpResponse(json.dumps(r._content),
                            status=r.status_code,
                            content_type='application/json')

    rewrite_list = build_rewrite_list(crosswalk)
    host_path = get_host_url(request, resource_type)[:-1]

    text_in = get_response_text(fhir_response=r)

    text_out = post_process_request(request,
                                    host_path,
                                    text_in,
                                    rewrite_list)

    return JsonResponse(text_out)
