import logging

from ..constants import ALLOWED_RESOURCE_TYPES, MAX_PAGE_SIZE
from ..decorators import require_valid_token
from ..errors import build_error_response

from apps.fhir.bluebutton.utils import (request_get_with_params,
                                        build_rewrite_list,
                                        get_crosswalk,
                                        get_host_url,
                                        get_resourcerouter,
                                        post_process_request,
                                        get_response_text,
                                        )
from apps.fhir.bluebutton.pagination import (get_page_size)

from rest_framework.decorators import throttle_classes, api_view
from apps.dot_ext.throttling import TokenRateThrottle
from urllib.parse import urlencode
from rest_framework import (exceptions, permissions)
from rest_framework.response import Response

from apps.fhir.bluebutton.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from apps.fhir.bluebutton.views.generic import FhirDataView
from ..permissions import (SearchCrosswalkPermission, ResourcePermission)

logger = logging.getLogger('hhs_server.%s' % __name__)

START_PARAMETER = 'startIndex'
SIZE_PARAMETER = 'count'


class SearchView(FhirDataView):
    permission_classes = [
        permissions.IsAuthenticated,
        ResourcePermission,
        SearchCrosswalkPermission,
    ]

    def get(self, request, resource_type, *args, **kwargs):
        # Verify paging inputs. Casting an invalid int will throw a ValueError
        try:
            start_index = int(request.GET.get(START_PARAMETER, 0))
        except ValueError:
            raise exceptions.ParseError(detail='%s must be an integer between zero and the number of results' % START_PARAMETER)

        if start_index < 0:
            raise exceptions.ParseError()

    try:
        page_size = get_page_size(request.GET)

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

        if page_size <= 0 or page_size > MAX_PAGE_SIZE:
            raise exceptions.ParseError()

        data = self.fetch_data(request, resource_type, *args, **kwargs)

        if data.get('total', 0) > 0:
            # TODO update to pagination class
            data['entry'] = data['entry'][start_index:start_index + page_size]
            replay_parameters = self.build_parameters(request)
            data['link'] = get_paging_links(request.build_absolute_uri('?'),
                                            start_index,
                                            page_size,
                                            data['total'],
                                            replay_parameters)

        return Response(data)

    def build_parameters(self, request, *args, **kwargs):
        patient_id = request.crosswalk.fhir_id
        resource_type = request.resource_type
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

    def build_url(self, resource_router, resource_type, *args, **kwargs):
        return resource_router.fhir_url + resource_type + "/"


def get_paging_links(base_url, start_index, page_size, count, replay_parameters):

    if base_url[-1] != '/':
        base_url += '/'

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
