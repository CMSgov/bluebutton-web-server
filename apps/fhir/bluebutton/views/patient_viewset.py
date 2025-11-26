from apps.fhir.bluebutton.views.viewsets_base import ResourceViewSet
from voluptuous import (
    Required,
    All,
    Match,
    Range,
    Coerce,
)
from apps.fhir.bluebutton.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from apps.authorization.permissions import DataAccessGrantPermission
from apps.capabilities.permissions import TokenHasProtectedCapability
from apps.fhir.bluebutton.permissions import (
    ReadCrosswalkPermission,
    SearchCrosswalkPermission,
    ResourcePermission,
    ApplicationActivePermission,
)
from rest_framework import permissions


class HasSearchScope(permissions.BasePermission):
    def has_permission(self, request, view) -> bool:  # type: ignore
        required_scopes = getattr(view, 'required_scopes', None)
        if required_scopes is None:
            return True

        if hasattr(request, 'auth') and request.auth is not None:
            token_scopes = request.auth.scope
            return any(scope in token_scopes for scope in required_scopes)
        return False


class PatientViewSet(ResourceViewSet):
    """Patient django-rest-framework ViewSet experiment

    Args:
        FhirDataView: Base mixin, unchanged
        viewsets: django-rest-framework ViewSet base class
    """

    resource_type = 'Patient'

    # TODO - I don't love the separation here, could be indicative that we don't want to move to resource based ViewSets, or that
    # we need a better base class, or these differences should be defined in PatientViewSet.
    REGEX_LASTUPDATED_VALUE = r'^((lt)|(le)|(gt)|(ge)).+'
    SEARCH_QUERY_TRANSFORMS = {
        'count': '_count',
    }
    SEARCH_QUERY_SCHEMA = {
        'startIndex': Coerce(int),
        Required('_count', default=DEFAULT_PAGE_SIZE): All(Coerce(int), Range(min=0, max=MAX_PAGE_SIZE)),  # type: ignore
        '_lastUpdated': [Match(REGEX_LASTUPDATED_VALUE, msg='the _lastUpdated operator is not valid')]
    }

    SEARCH_PERMISSION_CLASSES = (
        permissions.IsAuthenticated,
        ApplicationActivePermission,
        ResourcePermission,
        SearchCrosswalkPermission,
        DataAccessGrantPermission,
        TokenHasProtectedCapability,
        HasSearchScope,
    )

    READ_PERMISSION_CLASSES = (
        permissions.IsAuthenticated,
        ApplicationActivePermission,
        ResourcePermission,
        ReadCrosswalkPermission,
        DataAccessGrantPermission,
        TokenHasProtectedCapability,
    )

    required_scopes = ['patient/Patient.read', 'patient/Patient.rs', 'patient/Patient.s']

    def __init__(self, version, **kwargs):
        super().__init__(version)

    def build_url(self, fhir_settings, resource_type, resource_id=None, *args, **kwargs):
        if fhir_settings.fhir_url.endswith('v1/fhir/'):
            # only if called by tests
            return '{}{}/{}/'.format(fhir_settings.fhir_url, resource_type, resource_id)
        else:
            if self.version == 3 and getattr(fhir_settings, 'fhir_url_v3', None):
                fhir_url = fhir_settings.fhir_url_v3
            else:
                fhir_url = fhir_settings.fhir_url

            if resource_id:
                return f"{fhir_url}/v{self.version}/fhir/{resource_type}/{resource_id}/"
            else:
                return f"{fhir_url}/v{self.version}/fhir/{resource_type}/"
