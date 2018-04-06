from rest_framework.response import Response
import requests
import logging

from ..constants import ALLOWED_RESOURCE_TYPES
from ..decorators import require_valid_token
from ..errors import build_error_response

from apps.fhir.bluebutton.utils import (build_fhir_response,
                                        FhirServerVerify,
                                        get_crosswalk,
                                        get_resourcerouter)
from apps.fhir.bluebutton.serializers import localize

import apps.fhir.server.connection as backend_connection
from apps.fhir.parsers import FHIRParser
from apps.fhir.renderers import FHIRRenderer

from rest_framework.decorators import throttle_classes, api_view, parser_classes, renderer_classes
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from rest_framework import exceptions

from apps.dot_ext.throttling import TokenRateThrottle

logger = logging.getLogger('hhs_server.%s' % __name__)


#####################################################################
# These functions are a stepping stone to a single class based view #
#####################################################################
def check_resource_permission(request, resource_type=None, resource_id=None, **kwargs):
    crosswalk = get_crosswalk(request.resource_owner)

    # If the user isn't matched to a backend ID, they have no permissions
    if crosswalk is None:
        logger.info('Crosswalk for %s does not exist' % request.user)
        raise exceptions.PermissionDenied(
            'No access information was found for the authenticated user')

    if resource_type == 'Patient':
        # Error out in advance for non-matching Patient records.
        # Other records must hit backend to check permissions.
        if resource_id != crosswalk.fhir_id:
            raise exceptions.PermissionDenied(
                'You do not have permission to access data on the requested patient')
    return crosswalk


def build_parameters(**kwargs):
    return {
        "_format": "json"
    }


def build_url(resource_router, resource_type=None, resource_id=None, **kwargs):
    return resource_router.fhir_url + resource_type + "/" + resource_id + "/"


@require_valid_token()
@api_view(['GET'])
@parser_classes([JSONParser, FHIRParser])
@renderer_classes([JSONRenderer, FHIRRenderer])
@throttle_classes([TokenRateThrottle])
def read(request, resource_type, resource_id, *args, **kwargs):
    # reset request back to django.HttpRequest
    request = request._request
    """
    Read from Remote FHIR Server
    # Example client use in curl:
    # curl -X GET http://127.0.0.1:8000/fhir/Patient/1234
    """

    logger.debug("resource_type: %s" % resource_type)
    logger.debug("Interaction: read")
    logger.debug("Request.path: %s" % request.path)

# VALIDATION

    crosswalk = check_resource_permission(request,
                                          resource_type=resource_type,
                                          resource_id=resource_id)

# END VALIDATION

# RETRIEVE RESOURCE

    if resource_type not in ALLOWED_RESOURCE_TYPES:
        logger.info('User requested read access to the %s resource type' % resource_type)
        return build_error_response(404, 'The requested resource type, %s, is not supported'
                                         % resource_type)

    resource_router = get_resourcerouter(crosswalk)
    target_url = build_url(resource_router,
                           resource_type=resource_type,
                           resource_id=resource_id)

    logger.debug('FHIR URL with key:%s' % target_url)

    get_parameters = build_parameters()

    logger.debug('Here is the URL to send, %s now add '
                 'GET parameters %s' % (target_url, get_parameters))

    # Now make the call to the backend API
    r = requests.get(target_url,
                     params=get_parameters,
                     cert=backend_connection.certs(crosswalk=crosswalk),
                     headers=backend_connection.headers(request, url=target_url),
                     timeout=resource_router.wait_time,
                     verify=FhirServerVerify(crosswalk=crosswalk))
    response = build_fhir_response(request, target_url, crosswalk, r=r, e=None)

    if response.status_code == 404:
        return build_error_response(404, 'The requested resource does not exist')

    # TODO: This should be more specific
    if response.status_code >= 300:
        return build_error_response(502, 'An error occurred contacting the upstream server')

    # Now check that the user has permission to access the data
    # Patient resources were taken care of above
    # Return 404 on error to avoid notifying unauthorized user the object exists
    try:
        if resource_type == 'Coverage':
            reference = response._json()['beneficiary']['reference']
            reference_id = reference.split('/')[1]
            if reference_id != crosswalk.fhir_id:
                return standard_404()
        elif resource_type == 'ExplanationOfBenefit':
            reference = response._json()['patient']['reference']
            reference_id = reference.split('/')[1]
            if reference_id != crosswalk.fhir_id:
                return standard_404()
    except Exception:
        logger.warning('An error occurred fetching beneficiary id')
        return standard_404()

# END RETRIEVE RESOURCE

# SERIALIZATION

    text_out = localize(request=request,
                        response=response,
                        crosswalk=crosswalk,
                        resource_type=resource_type)

# END SERIALIZATION
    return Response(text_out)


def standard_404():
    return build_error_response(404, 'The requested resource does not exist')
