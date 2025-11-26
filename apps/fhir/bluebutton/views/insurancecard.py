from apps.fhir.bluebutton.views.generic import FhirDataView
from apps.fhir.bluebutton.permissions import (SearchCrosswalkPermission,
                                              ResourcePermission,
                                              ApplicationActivePermission)
from apps.authorization.permissions import DataAccessGrantPermission
from apps.capabilities.permissions import TokenHasProtectedCapability

from rest_framework import permissions


class HasDigitalInsuranceCardScope(permissions.BasePermission):
    def has_permission(self, request, view) -> bool:  # type: ignore
        # TODO - implement scope checking logic
        return True


class DigitalInsuranceCardSearchView(FhirDataView):
    '''Digital Insurance Card view for handling BFD Endpoint'''

    permission_classes = [
        permissions.IsAuthenticated,
        ApplicationActivePermission,
        ResourcePermission,
        SearchCrosswalkPermission,
        DataAccessGrantPermission,
        TokenHasProtectedCapability,
        HasDigitalInsuranceCardScope,
    ]

    required_coverage_search_scopes = ['patient/Coverage.rs', 'patient/Coverage.s', 'patient/Coverage.read']
    required_patient_read_scopes = ['patient/Patient.r', 'patient/Patient.rs', 'patient/Patient.read']

    def __init__(self, version=1):
        super().__init__(version)
        self.resource_type = 'Bundle'

    def has_permission(self, request, view):
        required_scopes = getattr(view, 'required_scopes', None)
        if required_scopes is None:
            return False
        return request.user.is_authenticated and hasattr(request.user, 'crosswalk')

    def build_parameters(self, request):
        return {
            '_format': 'application/json'
        }

    def build_url(self, fhir_settings, resource_type, resource_id=None, *args, **kwargs):
        if fhir_settings.fhir_url.endswith('v1/fhir/'):
            # only if called by tests
            return f"{fhir_settings.fhir_url}{resource_type}/"
        else:
            if self.version == 3 and getattr(fhir_settings, 'fhir_url_v3', None):
                fhir_url = fhir_settings.fhir_url_v3
            else:
                fhir_url = fhir_settings.fhir_url
            return f"{fhir_url}/v{self.version}/fhir/Patient/{resource_id}/$generate-insurance-card"
