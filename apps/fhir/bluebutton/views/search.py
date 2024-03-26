from datetime import datetime
from voluptuous import (
    Required,
    All,
    Match,
    Range,
    Coerce,
    Schema,
    REMOVE_EXTRA,
)
from rest_framework import (permissions)
from rest_framework.response import Response

from apps.fhir.bluebutton.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from apps.fhir.bluebutton.views.generic import FhirDataView
from apps.authorization.permissions import DataAccessGrantPermission
from apps.capabilities.permissions import TokenHasProtectedCapability
from ..permissions import (SearchCrosswalkPermission, ResourcePermission, ApplicationActivePermission)


class SearchView(FhirDataView):
    # Base class for FHIR resource search views

    # BB2-149 note, check authenticated first, then app active etc.
    permission_classes = [
        permissions.IsAuthenticated,
        ApplicationActivePermission,
        ResourcePermission,
        SearchCrosswalkPermission,
        DataAccessGrantPermission,
        TokenHasProtectedCapability,
    ]

    # Regex to match a valid _lastUpdated value that can begin with lt, le, gt and ge operators
    REGEX_LASTUPDATED_VALUE = r'^((lt)|(le)|(gt)|(ge)).+'

    QUERY_TRANSFORMS = {
        'count': '_count',
    }

    QUERY_SCHEMA = {
        Required('startIndex', default=0): Coerce(int),
        Required('_count', default=DEFAULT_PAGE_SIZE): All(Coerce(int), Range(min=0, max=MAX_PAGE_SIZE)),
        '_lastUpdated': [Match(REGEX_LASTUPDATED_VALUE, msg="the _lastUpdated operator is not valid")]
    }

    def __init__(self, version=1):
        self.resource_type = None
        super().__init__(version)

    def initial(self, request, *args, **kwargs):
        return super().initial(request, self.resource_type, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return super().get(request, self.resource_type, *args, **kwargs)

    def build_url(self, resource_router, resource_type, *args, **kwargs):
        if resource_router.fhir_url.endswith('v1/fhir/'):
            # only if called by tests
            return "{}{}/".format(resource_router.fhir_url, resource_type)
        else:
            return "{}/{}/fhir/{}/".format(resource_router.fhir_url, 'v2' if self.version == 2 else 'v1',
                                           resource_type)


class SearchViewInsurancePatient(SearchView):
    # Class used for Patient resource search view
    PATIENT_KEYS = ['meta', 'name', 'id']

    def __init__(self, version=1):
        super().__init__(version)
        self.resource_type = "Patient"

    def build_parameters(self, request, *args, **kwargs):
        return {
            '_format': 'application/json+fhir',
            '_id': request.crosswalk.fhir_id,
        }

    def get(self, request, *args, **kwargs):
        patient = super().get(request, *args, **kwargs)
        patient_resource = patient.data['entry'][0]['resource']
        filtered_patient = {key: patient_resource[key] for key in self.PATIENT_KEYS}
        return Response(filtered_patient)


class SearchViewInsuranceCoverage(SearchView):
    # Class used for Coverage resource search view
    COVERAGE_KEYS = ['status', 'type', 'subscriberId', 'relationship', 'payor', 'class']

    def __init__(self, version=1):
        super().__init__(version)
        self.resource_type = "Coverage"

    def build_parameters(self, request, *args, **kwargs):
        return {
            '_format': 'application/json+fhir',
            'beneficiary': 'Patient/' + request.crosswalk.fhir_id,
        }

    def get(self, request, *args, **kwargs):
        coverage = super().get(request, *args, **kwargs)
        out_data = []
        for entry in coverage.data['entry']:
            coverage_resource = entry['resource']
            filtered_coverage = {key: coverage_resource[key] for key in self.COVERAGE_KEYS}
            filtered_coverage['period'] = '05-10-2020'
            out_data.append(filtered_coverage)
        return Response(out_data)


class SearchViewInsuranceOrganization(SearchView):

        def __init__(self, version=1):
            super().__init__(version)
            self.resource_type = "Coverage"

        def get(self, request, *args, **kwargs):
            out_data = [{'active': 'true', 'name': 'Centers for Medicare and Medicaid Services'}]
            return Response(out_data)


class SearchViewPatient(SearchView):
    # Class used for Patient resource search view

    def __init__(self, version=1):
        super().__init__(version)
        self.resource_type = "Patient"

    def build_parameters(self, request, *args, **kwargs):
        return {
            '_format': 'application/json+fhir',
            '_id': request.crosswalk.fhir_id,
        }


class SearchViewCoverage(SearchView):
    # Class used for Coverage resource search view

    def __init__(self, version=1):
        super().__init__(version)
        self.resource_type = "Coverage"

    def build_parameters(self, request, *args, **kwargs):
        return {
            '_format': 'application/json+fhir',
            'beneficiary': 'Patient/' + request.crosswalk.fhir_id,
        }


class SearchViewExplanationOfBenefit(SearchView):
    # Class used for ExplanationOfBenefit resource search view

    # Regex to match a valid type value
    REGEX_TYPE_VALUE = r"(carrier)|" + \
        r"(pde)|" + \
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
    REGEX_TYPE_VALUES_LIST = r'(?i)^((' + REGEX_TYPE_VALUE + r')\s*,*\s*)+$'

    # Regex to match a valid service-date value that can begin with lt, le, gt and ge operators
    REGEX_SERVICE_DATE_VALUE = r'^((lt)|(le)|(gt)|(ge)).+'

    # Add type parameter to schema only for EOB
    QUERY_SCHEMA = {**SearchView.QUERY_SCHEMA,
                    'type': Match(REGEX_TYPE_VALUES_LIST, msg="the type parameter value is not valid"),
                    'service-date': [Match(REGEX_SERVICE_DATE_VALUE, msg="the service-date operator is not valid")]
                    }

    def __init__(self, version=1):
        super().__init__(version)
        self.resource_type = "ExplanationOfBenefit"

    def build_parameters(self, request, *args, **kwargs):
        return {
            '_format': 'application/json+fhir',
            'patient': request.crosswalk.fhir_id,
        }

    def filter_parameters(self, request):
        params = self.map_parameters(request.query_params.dict())
        # Get list from _lastUpdated QueryDict(), since it can have multi params
        params['_lastUpdated'] = request.query_params.getlist('_lastUpdated')
        # Get list from service-date QueryDict(), since it can have multi params
        service_dates = request.query_params.getlist('service-date')
        if service_dates:
            params['service-date'] = service_dates

        schema = Schema(
            getattr(self, "QUERY_SCHEMA", {}),
            extra=REMOVE_EXTRA)
        return schema(params)
