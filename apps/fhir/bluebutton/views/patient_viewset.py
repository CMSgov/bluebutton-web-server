from apps.fhir.bluebutton.views.viewsets_base import ResourceViewSet
from apps.fhir.bluebutton.views.search import HasSearchScope, SearchView
from apps.authorization.permissions import DataAccessGrantPermission
from apps.capabilities.permissions import TokenHasProtectedCapability
from apps.fhir.bluebutton.permissions import (
    ReadCrosswalkPermission,
    SearchCrosswalkPermission,
    ResourcePermission,
    ApplicationActivePermission,
)
from rest_framework import permissions


class PatientViewSet(ResourceViewSet):
    """Patient django-rest-framework ViewSet experiment

    Args:
        FhirDataView: Base mixin, unchanged
        viewsets: django-rest-framework ViewSet base class
    """

    version = 1
    resource_type = 'Patient'

    # TODO - I don't love the separation here, could be indicative that we don't want to move to resource based ViewSets, or that
    # we need a better base class, or these differences should be defined in PatientViewSet.
    SEARCH_QUERY_TRANSFORMS = getattr(SearchView, 'QUERY_TRANSFORMS', {})
    SEARCH_QUERY_SCHEMA = {**getattr(SearchView, 'QUERY_SCHEMA', {}), '_id': str, 'identifier': str}

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
