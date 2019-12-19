import logging

from voluptuous import (
    Required,
    All,
    Range,
    Coerce,
    Any,
)
from rest_framework import (permissions)

from apps.fhir.bluebutton.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from apps.fhir.bluebutton.views.generic import FhirDataView
from apps.authorization.permissions import DataAccessGrantPermission
from apps.capabilities.permissions import TokenHasProtectedCapability
from ..permissions import (SearchCrosswalkPermission, ResourcePermission)

logger = logging.getLogger('hhs_server.%s' % __name__)


class SearchView(FhirDataView):
    permission_classes = [
        permissions.IsAuthenticated,
        ResourcePermission,
        SearchCrosswalkPermission,
        DataAccessGrantPermission,
        TokenHasProtectedCapability,
    ]

    query_transforms = {
        'count': '_count',
    }

    query_schema = {
        Required('startIndex', default=0): Coerce(int),
        Required('_count', default=DEFAULT_PAGE_SIZE): All(Coerce(int), Range(min=0, max=MAX_PAGE_SIZE)),
        'type': Any(
            'carrier',
            'pde',
            'dme',
            'hha',
            'hospice',
            'inpatient',
            'outpatient',
            'snf',
            'https://bluebutton.cms.gov/resources/codesystem/eob-type|',
            'https://bluebutton.cms.gov/resources/codesystem/eob-type|carrier',
            'https://bluebutton.cms.gov/resources/codesystem/eob-type|pde',
            'https://bluebutton.cms.gov/resources/codesystem/eob-type|dme',
            'https://bluebutton.cms.gov/resources/codesystem/eob-type|hha',
            'https://bluebutton.cms.gov/resources/codesystem/eob-type|hospice',
            'https://bluebutton.cms.gov/resources/codesystem/eob-type|inpatient',
            'https://bluebutton.cms.gov/resources/codesystem/eob-type|outpatient',
            'https://bluebutton.cms.gov/resources/codesystem/eob-type|snf',
        ),
    }

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
