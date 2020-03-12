import logging

from voluptuous import (
    Required,
    All,
    Match,
    Range,
    Coerce,
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

    # Regex to match a valid type value
    regex_type_value = r"(carrier)|" + \
        r"(pde)|" + \
        r"(https://bluebutton.cms.gov/resources/codesystem/eob-type\|pde)" + \
        r"(dme)|" + \
        r"(hha)|" + \
        r"(hospice)|" + \
        r"(inpatient)|" + \
        r"(outpatient)|" + \
        r"(snf)|" + \
        r"(https://bluebutton.cms.gov/resources/codesystem/eob-type\|)|" + \
        r"(https://bluebutton.cms.gov/resources/codesystem/eob-type\|carrier)|" + \
        r"(https://bluebutton.cms.gov/resources/codesystem/eob-type\|pde)|" + \
        r"(https://bluebutton.cms.gov/resources/codesystem/eob-type\|dme)|" + \
        r"(https://bluebutton.cms.gov/resources/codesystem/eob-type\|hha)|" + \
        r"(https://bluebutton.cms.gov/resources/codesystem/eob-type\|hospice)|" + \
        r"(https://bluebutton.cms.gov/resources/codesystem/eob-type\|inpatient)|" + \
        r"(https://bluebutton.cms.gov/resources/codesystem/eob-type\|outpatient)|" + \
        r"(https://bluebutton.cms.gov/resources/codesystem/eob-type\|snf)"

    # Regex to match a list of comma separated type values with IGNORECASE
    regex_type_values_list = r'(?i)^((' + regex_type_value + r')\s*,*\s*)+$'

    # Regex to match a valid _lastUpdated value that can begin with
    # lt, le, gt and ge operators
    regex_lastupdated_value = r'^((lt)|(le)|(gt)|(ge)).+'

    query_transforms = {
        'count': '_count',
    }

    query_schema = {
        Required('startIndex', default=0): Coerce(int),
        Required('_count', default=DEFAULT_PAGE_SIZE): All(Coerce(int), Range(min=0, max=MAX_PAGE_SIZE)),
        'type': Match(regex_type_values_list, msg="the type parameter value is not valid"),
        '_lastUpdated': [Match(regex_lastupdated_value, msg="the _lastUpdated operator is not valid")],
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
