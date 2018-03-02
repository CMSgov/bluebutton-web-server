from rest_framework.response import Response
import logging

from ..constants import ALLOWED_RESOURCE_TYPES, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from ..decorators import require_valid_token
from ..errors import build_error_response

from apps.fhir.bluebutton.utils import (request_get_with_params,
                                        build_rewrite_list,
                                        get_crosswalk,
                                        get_host_url,
                                        get_resourcerouter,
                                        post_process_request,
                                        get_response_text)
from apps.fhir.parsers import FHIRParser
from apps.fhir.renderers import FHIRRenderer

from rest_framework.decorators import throttle_classes, api_view, parser_classes, renderer_classes
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer

from apps.dot_ext.throttling import TokenRateThrottle
from urllib.parse import urlencode

logger = logging.getLogger('hhs_server.%s' % __name__)

START_PARAMETER = 'startIndex'
SIZE_PARAMETER = 'count'


@require_valid_token()
@api_view(['GET'])
@parser_classes([JSONParser, FHIRParser])
@renderer_classes([JSONRenderer, FHIRRenderer])
@throttle_classes([TokenRateThrottle])
def search(request, resource_type, *args, **kwargs):
    # reset request back to django.HttpRequest
    request = request._request
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

    # Get parameters required to replay request for relative links
    replay_parameters = {}

    # If the user isn't matched to a backend ID, they have no permissions
    if crosswalk is None:
        logger.info('Crosswalk for %s does not exist' % request.user)
        return build_error_response(403, 'No access information was found for the authenticated user')

    # Verify paging inputs. Casting an invalid int will throw a ValueError
    try:
        start_index = int(request.GET.get(START_PARAMETER, 0))
        if start_index < 0:
            raise ValueError
    except ValueError:
        return build_error_response(400, '%s must be an integer between zero and the number of results' % START_PARAMETER)

    try:
        page_size = int(request.GET.get(SIZE_PARAMETER, DEFAULT_PAGE_SIZE))
        if page_size <= 0 or page_size > MAX_PAGE_SIZE:
            raise ValueError
    except ValueError:
        return build_error_response(400, '%s must be an integer between 1 and %s' % (SIZE_PARAMETER, MAX_PAGE_SIZE))

    resource_router = get_resourcerouter(crosswalk)
    target_url = resource_router.fhir_url + resource_type + "/"

    get_parameters = {
        '_format': 'application/json+fhir'
    }

    patient_id = crosswalk.fhir_id

    if 'patient' in request.GET and request.GET['patient'] != patient_id:
        return build_error_response(403, 'You do not have permission to access the requested patient\'s data')

    if resource_type == 'ExplanationOfBenefit':
        replay_parameters['patient'] = patient_id
        get_parameters['patient'] = patient_id
    elif resource_type == 'Coverage':
        get_parameters['beneficiary'] = 'Patient/' + patient_id
        replay_parameters['beneficiary'] = 'Patient/' + patient_id
        if 'beneficiary' in request.GET and patient_id not in request.GET['beneficiary']:
            return build_error_response(403, 'You do not have permission to access the requested patient\'s data')
    elif resource_type == 'Patient':
        get_parameters['_id'] = patient_id

    response = request_get_with_params(request,
                                       target_url,
                                       get_parameters,
                                       crosswalk,
                                       timeout=resource_router.wait_time)

    if response.status_code >= 300:
        logger.debug("We have an error code to deal with: %s" % response.status_code)
        return build_error_response(response.status_code,
                                    'An error occurred while contacting our data server',
                                    details=response._content)

    rewrite_list = build_rewrite_list(crosswalk)
    host_path = get_host_url(request, resource_type)[:-1]

    text_in = get_response_text(fhir_response=response)

    out_data = post_process_request(request,
                                    host_path,
                                    text_in,
                                    rewrite_list)

    out_data['entry'] = out_data['entry'][start_index:start_index + page_size]
    out_data['link'] = get_paging_links(request.build_absolute_uri('?'),
                                        start_index,
                                        page_size,
                                        out_data['total'],
                                        replay_parameters)

    return Response(out_data)


def get_paging_links(base_url, start_index, page_size, count, replay_parameters):
    out = []
    replay_parameters[SIZE_PARAMETER] = page_size

    replay_parameters[START_PARAMETER] = start_index
    out.append({
        'relation': 'self',
        'url': base_url + '?' + urlencode(replay_parameters)
    })

    if start_index + page_size < count:
        replay_parameters[START_PARAMETER] = start_index + page_size
        out.append({
            'relation': 'next',
            'url': base_url + '?' + urlencode(replay_parameters)
        })

    if start_index - page_size >= 0:
        replay_parameters[START_PARAMETER] = start_index - page_size
        out.append({
            'relation': 'previous',
            'url': base_url + '?' + urlencode(replay_parameters)
        })

    if start_index > 0:
        replay_parameters[START_PARAMETER] = 0
        out.append({
            'relation': 'first',
            'url': base_url + '?' + urlencode(replay_parameters)
        })

    # This formula rounds count down to the nearest multiple of page_size
    # that's less than and not equal to count
    last_index = (count - 1) // page_size * page_size
    if start_index < last_index:
        replay_parameters[START_PARAMETER] = last_index
        out.append({
            'relation': 'last',
            'url': base_url + '?' + urlencode(replay_parameters)
        })

    return out
