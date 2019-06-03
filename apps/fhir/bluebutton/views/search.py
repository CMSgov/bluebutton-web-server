import logging

from urllib.parse import urlencode
from rest_framework import (exceptions, permissions)
from rest_framework.response import Response

from apps.fhir.bluebutton.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from apps.fhir.bluebutton.views.generic import FhirDataView
from apps.authorization.permissions import DataAccessGrantPermission
from ..permissions import (SearchCrosswalkPermission, ResourcePermission)

logger = logging.getLogger('hhs_server.%s' % __name__)

START_PARAMETER = 'startIndex'
SIZE_PARAMETER = '_count'

QUERY_TRANSFORMS = {
    'count': '_count',
}

# startIndex must be an int that defaults to 0
# _count must be an int between 0 and MAX_PAGE_SIZE and defaults to DEFAULT_PAGE_SIZE
# if count is pass transform it into _count before passing on to data server

class ParamSerializer(object):
    # conforming to the basics of http://www.django-rest-framework.org/api-guide/serializers/#validation
    def __init__(self, data=None, **kwargs):
        self.initial_data = data
        self.data = {}

    def is_valid(self, raise_exception=False, **kwargs):
        for key, val in self.initial_data.items():
            self.data[key] = val

        for key, correct in QUERY_TRANSFORMS.items():
            val = self.data.pop(key, None)
            if val is not None:
                self.data[correct] = val

query_schema = Schema({
    Required("_count", default=DEFAULT_PAGE_SIZE): All(Clamp(min=0, max=MAX_PAGE_SIZE), Coerce(int)),
    Required("startIndex", default=0): Coerce(int),
})
def query_transform(data):
        for key, correct in QUERY_TRANSFORMS.items():
            val = data.pop(key, None)
            if val is not None:
                data[correct] = val




class SearchView(FhirDataView):
    permission_classes = [
        permissions.IsAuthenticated,
        ResourcePermission,
        SearchCrosswalkPermission,
        DataAccessGrantPermission,
    ]

    def get(self, request, resource_type, *args, **kwargs):
        query_params = query_schema(query_transform(request.query_params, QUERY_TRANSFORMS))

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
