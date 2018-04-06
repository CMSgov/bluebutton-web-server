from rest_framework.response import Response
import copy
import requests
import logging
import apps.fhir.server.connection as backend_connection

from ..constants import ALLOWED_RESOURCE_TYPES, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from ..decorators import require_valid_token
from ..errors import build_error_response

from apps.fhir.bluebutton.utils import (build_fhir_response,
                                        FhirServerVerify,
                                        get_crosswalk,
                                        get_resourcerouter)
from apps.fhir.bluebutton.serializers import localize
from apps.fhir.parsers import FHIRParser
from apps.fhir.renderers import FHIRRenderer

from rest_framework.decorators import throttle_classes, api_view, parser_classes, renderer_classes
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from rest_framework import exceptions

from apps.dot_ext.throttling import TokenRateThrottle
from urllib.parse import urlencode

logger = logging.getLogger('hhs_server.%s' % __name__)

START_PARAMETER = 'startIndex'
SIZE_PARAMETER = 'count'


#####################################################################
# These functions are a stepping stone to a single class based view #
#####################################################################
def check_resource_permission(request, **kwargs):
    crosswalk = get_crosswalk(request.resource_owner)

    # If the user isn't matched to a backend ID, they have no permissions
    if crosswalk is None:
        logger.info('Crosswalk for %s does not exist' % request.user)
        raise exceptions.PermissionDenied(
            'No access information was found for the authenticated user')

    patient_id = crosswalk.fhir_id

    if 'patient' in request.GET and request.GET['patient'] != patient_id:
        raise exceptions.PermissionDenied(
            'You do not have permission to access the requested patient\'s data')

    if 'beneficiary' in request.GET and patient_id not in request.GET['beneficiary']:
        raise exceptions.PermissionDenied(
            'You do not have permission to access the requested patient\'s data')
    return crosswalk


def build_parameters(patient_id=None, resource_type=None, **kwargs):
    get_parameters = {
        '_format': 'application/json+fhir'
    }

    if resource_type == 'ExplanationOfBenefit':
        get_parameters['patient'] = patient_id
    elif resource_type == 'Coverage':
        get_parameters['beneficiary'] = 'Patient/' + patient_id
    elif resource_type == 'Patient':
        get_parameters['_id'] = patient_id
    return get_parameters


def build_url(resource_router, resource_type=None, **kwargs):
    return resource_router.fhir_url + resource_type + "/"


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

# VALIDATION
    
    crosswalk = check_resource_permission(request)

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

# END VALIDATION

# RETRIEVE RESOURCE

    if resource_type not in ALLOWED_RESOURCE_TYPES:
        logger.info('User requested search access to the %s resource type' % resource_type)
        return build_error_response(404, 'The requested resource type, %s, is not supported'
                                         % resource_type)

    resource_router = get_resourcerouter(crosswalk)
    target_url = build_url(resource_router, resource_type=resource_type)

    get_parameters = build_parameters(patient_id=crosswalk.fhir_id,
                                      resource_type=resource_type)

    replay_parameters = copy.deepcopy(get_parameters)

    r = requests.get(target_url,
                     params=get_parameters,
                     cert=backend_connection.certs(crosswalk=crosswalk),
                     headers=backend_connection.headers(request, url=target_url),
                     timeout=resource_router.wait_time,
                     verify=FhirServerVerify(crosswalk=crosswalk))
    response = build_fhir_response(request, target_url, crosswalk, r=r, e=None)

    if response.status_code >= 300:
        logger.debug("We have an error code to deal with: %s" % response.status_code)
        return build_error_response(response.status_code,
                                    'An error occurred while contacting our data server',
                                    details=response._content)
# END RETRIEVE RESOURCE

# SERIALIZATION

    out_data = localize(request=request,
                        response=response,
                        crosswalk=crosswalk,
                        resource_type=resource_type)
# END SERIALIZATION

# PAGINATION
    out_data['entry'] = out_data['entry'][start_index:start_index + page_size]
    out_data['link'] = get_paging_links(request.build_absolute_uri('?'),
                                        start_index,
                                        page_size,
                                        out_data['total'],
                                        replay_parameters)

# END PAGINATION
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
