from rest_framework import viewsets, permissions
from rest_framework.response import Response

from apps.fhir.bluebutton.views.generic import FhirDataView
from apps.fhir.bluebutton.views.search import HasSearchScope, SearchView
from apps.authorization.permissions import DataAccessGrantPermission
from apps.capabilities.permissions import TokenHasProtectedCapability
from apps.fhir.bluebutton.permissions import (
    ReadCrosswalkPermission,
    SearchCrosswalkPermission,
    ResourcePermission,
    ApplicationActivePermission,
)


class PatientViewSet(FhirDataView, viewsets.ViewSet):
    """Patient django-rest-framework ViewSet experiment

    Args:
        FhirDataView: Base mixin, unchanged
        viewsets: django-rest-framework ViewSet base class
    """

    version = 1
    resource_type = 'Patient'

    QUERY_TRANSFORMS = getattr(SearchView, 'QUERY_TRANSFORMS', {})
    QUERY_SCHEMA = {**getattr(SearchView, 'QUERY_SCHEMA', {}), '_id': str, 'identifier': str}

    required_scopes = ['patient/Patient.read', 'patient/Patient.rs', 'patient/Patient.s']

    def __init__(self, version=1, **kwargs):
        super().__init__(version)

    def initial(self, request, *args, **kwargs):
        return super().initial(request, self.resource_type, *args, **kwargs)

    def get_permissions(self):
        action = getattr(self, 'action', None)
        if action == 'list':
            perm_classes = [
                permissions.IsAuthenticated,
                ApplicationActivePermission,
                ResourcePermission,
                SearchCrosswalkPermission,
                DataAccessGrantPermission,
                TokenHasProtectedCapability,
                HasSearchScope,
            ]
        else:
            perm_classes = [
                permissions.IsAuthenticated,
                ApplicationActivePermission,
                ResourcePermission,
                ReadCrosswalkPermission,
                DataAccessGrantPermission,
                TokenHasProtectedCapability,
            ]
        return [p() for p in perm_classes]

    def list(self, request, *args, **kwargs):
        out = self.fetch_data(request, self.resource_type, *args, **kwargs)
        return Response(out)

    def retrieve(self, request, resource_id=None, *args, **kwargs):
        out = self.fetch_data(request, self.resource_type, resource_id=resource_id, *args, **kwargs)
        return Response(out)

    def build_parameters(self, request):
        return {'_format': 'application/json+fhir'}

    def build_url(self, fhir_settings, resource_type, resource_id=None, *args, **kwargs):
        # Similar to the previous SearchView / ReadView implementations
        if fhir_settings.fhir_url.endswith('v1/fhir/'):
            if resource_id:
                return f"{fhir_settings.fhir_url}{resource_type}/{resource_id}/"
            else:
                return f"{fhir_settings.fhir_url}{resource_type}/"
        else:
            if self.version == 3 and getattr(fhir_settings, 'fhir_url_v3', None):
                fhir_url = fhir_settings.fhir_url_v3
            else:
                fhir_url = fhir_settings.fhir_url

            if resource_id:
                return f"{fhir_url}/v{self.version}/fhir/{resource_type}/{resource_id}/"
            else:
                return f"{fhir_url}/v{self.version}/fhir/{resource_type}/"
