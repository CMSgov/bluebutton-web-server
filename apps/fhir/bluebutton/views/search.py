import waffle

from voluptuous import (
    Required,
    All,
    Match,
    Range,
    Coerce,
    Schema,
    Invalid,
    REMOVE_EXTRA,
)
from rest_framework import (permissions)

from apps.fhir.bluebutton.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from apps.fhir.bluebutton.views.generic import FhirDataView
from apps.authorization.permissions import DataAccessGrantPermission
from apps.capabilities.permissions import TokenHasProtectedCapability
from ..permissions import (SearchCrosswalkPermission, ResourcePermission, ApplicationActivePermission)


class HasSearchScope(permissions.BasePermission):
    def has_permission(self, request, view):
        required_scopes = getattr(view, 'required_scopes', None)
        if required_scopes is None:
            return True

        if hasattr(request, 'auth') and request.auth is not None:
            token_scopes = request.auth.scope
            return any(scope in token_scopes for scope in required_scopes)
        return False


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
        HasSearchScope
    ]

    # Regex to match a valid _lastUpdated value that can begin with lt, le, gt and ge operators
    REGEX_LASTUPDATED_VALUE = r'^((lt)|(le)|(gt)|(ge)).+'

    QUERY_TRANSFORMS = {
        'count': '_count',
    }

    QUERY_SCHEMA = {
        'startIndex': Coerce(int),
        Required('_count', default=DEFAULT_PAGE_SIZE): All(Coerce(int), Range(min=0, max=MAX_PAGE_SIZE)),
        '_lastUpdated': [Match(REGEX_LASTUPDATED_VALUE, msg='the _lastUpdated operator is not valid')]
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
            if self.version == 3 and resource_router.fhir_url_v3:
                fhir_url = resource_router.fhir_url_v3
            else:
                fhir_url = resource_router.fhir_url
            return f"{fhir_url}/v{self.version}/fhir/{resource_type}/"


class SearchViewPatient(SearchView):
    # Class used for Patient resource search view
    required_scopes = ['patient/Patient.read', 'patient/Patient.rs', 'patient/Patient.s']

    def __init__(self, version=1):
        super().__init__(version)
        self.resource_type = "Patient"

    def build_parameters(self, request, *args, **kwargs):
        return {
            '_format': 'application/json+fhir',
            # BB2-4166-TODO : this needs to use self.version to determine fhir_id
            '_id': request.crosswalk.fhir_id(2)
        }


class SearchViewCoverage(SearchView):
    # Class used for Coverage resource search view
    required_scopes = ['patient/Coverage.read', 'patient/Coverage.rs', 'patient/Coverage.s']

    def __init__(self, version=1):
        super().__init__(version)
        self.resource_type = "Coverage"

    def build_parameters(self, request, *args, **kwargs):
        return {
            '_format': 'application/json+fhir',
            # BB2-4166-TODO : this needs to use self.version to determine fhir_id
            'beneficiary': 'Patient/' + request.crosswalk.fhir_id(2)
        }


class SearchViewExplanationOfBenefit(SearchView):
    # customized validator for better error reporting
    def validate_tag(self):
        def validator(value):
            for v in value:
                if not (v in ["Adjudicated", "PartiallyAdjudicated"]):
                    msg = f"Invalid _tag value (='{v}'), 'PartiallyAdjudicated' or 'Adjudicated' expected."
                    raise Invalid(msg)
            return value
        return validator

    # Class used for ExplanationOfBenefit resource search view
    required_scopes = ['patient/ExplanationOfBenefit.read', 'patient/ExplanationOfBenefit.rs', 'patient/ExplanationOfBenefit.s']

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
                    'service-date': [Match(REGEX_SERVICE_DATE_VALUE, msg="the service-date operator is not valid")],
                    }

    def __init__(self, version=1):
        super().__init__(version)
        self.resource_type = "ExplanationOfBenefit"

    def build_parameters(self, request, *args, **kwargs):
        return {
            '_format': 'application/json+fhir',
            # BB2-4166-TODO : this needs to use version to determine fhir_id
            'patient': request.crosswalk.fhir_id(2),
        }

    def filter_parameters(self, request):
        params = self.map_parameters(request.query_params.dict())
        # Get list from _lastUpdated QueryDict(), since it can have multi params
        params['_lastUpdated'] = request.query_params.getlist('_lastUpdated')
        # Get list from service-date QueryDict(), since it can have multi params
        service_dates = request.query_params.getlist('service-date')
        if service_dates:
            params['service-date'] = service_dates

        query_schema = getattr(self, "QUERY_SCHEMA", {})

        if waffle.switch_is_active('bfd_v3_connectathon'):
            query_schema['_tag'] = self.validate_tag()
            # _tag if presents, is a string value
            params['_tag'] = request.query_params.getlist('_tag')

        schema = Schema(
            query_schema,
            extra=REMOVE_EXTRA)

        return schema(params)
