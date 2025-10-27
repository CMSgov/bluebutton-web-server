import json
import logging

from collections import OrderedDict
from urllib.parse import urlencode
from django.http import JsonResponse
from django.shortcuts import HttpResponse
from urllib.parse import urlparse
# from oauth2_provider.compat import urlparse
from apps.fhir.bluebutton import constants
from apps.fhir.bluebutton.utils import (request_call,
                                        prepend_q,
                                        get_resourcerouter,
                                        get_response_text,
                                        build_oauth_resource)
from apps.constants import Versions

import apps.logging.request_logger as bb2logging

logger = logging.getLogger(bb2logging.HHS_SERVER_LOGNAME_FMT.format(__name__))


def get_supported_resources(resources, resource_names):
    """ Filter resources for resource type matches """

    resource_list = []

    # if resource 'type in resource_names add resource to resource_list
    for resource in resources:
        resource_type = resource.get('type', [])
        if resource_type in resource_names:
            resource['interaction'] = [{'code': 'read'}, {'code': 'search-type'}]
            resource_list.append(resource)

    return resource_list


def conformance_filter(text_block):
    """ Filter FHIR Conformance Statement based on
        supported ResourceTypes
    """
    # TODO: This is fragile based on the structure of the resource.
    # A more robust way of pulling this apart as we increment versions
    # may be something to explore. Or, at least, handling possible key errors
    # when reaching multiple levels deep into a structure.
    resource_names = constants.ALLOWED_RESOURCE_TYPES
    ct = 0
    if text_block:
        if 'rest' in text_block:
            for k in text_block['rest']:
                for i, v in k.items():
                    if i == 'resource':
                        supp_resources = get_supported_resources(v, resource_names)
                        text_block['rest'][ct]['resource'] = supp_resources
                ct += 1
        else:
            text_block = ""
    else:
        text_block = ""

    return text_block


def _fhir_conformance(request, version=Versions.NOT_AN_API_VERSION, *args):
    """ Pull and filter fhir Conformance statement

    BaseStu3 = "CapabilityStatement"

    :param request:
    :param args:
    :param kwargs:
    :return:
    """
    crosswalk = None
    resource_router = get_resourcerouter()

    match version:
        case Versions.V1:
            fhir_url = resource_router.fhir_url
        case Versions.V2:
            fhir_url = resource_router.fhir_url
        case Versions.V3:
            fhir_url = resource_router.fhir_url_v3
        case _:
            return HttpResponse(
                json.dumps({
                    'error': f'Invalid API version: {version}'
                }),
                status=r.status_code,
                content_type='application/json')

    parsed_url = urlparse(fhir_url)
    call_to = None
    if parsed_url.path is not None:
        call_to = f'{parsed_url.scheme}://{parsed_url.netloc}/v{version}/fhir/metadata'
    else:
        # url with no path
        call_to = f'{fhir_url}/v{version}/fhir/metadata'

    pass_params = {'_format': 'json'}

    encoded_params = urlencode(pass_params)
    pass_params = prepend_q(encoded_params)

    r = request_call(request, call_to + pass_params, crosswalk)

    text_out = ''

    if r.status_code >= 300:
        logger.debug(f'We have an error code to deal with: {r.status_code}')
        return HttpResponse(json.dumps(r._content),
                            status=r.status_code,
                            content_type='application/json')

    text_in = get_response_text(fhir_response=r)

    text_out = json.loads(text_in, object_pairs_hook=OrderedDict)

    od = conformance_filter(text_out)

    # Append Security to ConformanceStatement
    security_endpoint = build_oauth_resource(request, format_type='json')
    od['rest'][0]['security'] = security_endpoint
    # Fix format values
    od['format'] = ['application/json', 'application/fhir+json']

    return JsonResponse(od)


def fhir_conformance_v1(request):
    return _fhir_conformance(request, version=Versions.V1)


def fhir_conformance_v2(request):
    return _fhir_conformance(request, version=Versions.V2)


def fhir_conformance_v3(request):
    return _fhir_conformance(request, version=Versions.V3)
