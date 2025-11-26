from rest_framework import viewsets, permissions
from apps.fhir.bluebutton.views.generic import FhirDataView
from apps.authorization.permissions import DataAccessGrantPermission
from apps.capabilities.permissions import TokenHasProtectedCapability
from apps.fhir.bluebutton.permissions import (
    SearchCrosswalkPermission,
    ResourcePermission,
    ApplicationActivePermission,
)


class HasDigitalInsuranceCardScope(permissions.BasePermission):
    def has_permission(self, request, view) -> bool:  # type: ignore
        # TODO - implement scope checking logic
        return True


class DigitalInsuranceCardViewSet(FhirDataView, viewsets.ViewSet):
    """Digital Insurance Card (bundle) django-rest-framework ViewSet experiment

    Args:
        FhirDataView: Base mixin, unchanged
        viewsets: django-rest-framework ViewSet base class
    """

    version = 1
    resource_type = 'Bundle'

    required_coverage_search_scopes = ['patient/Coverage.rs', 'patient/Coverage.s', 'patient/Coverage.read']
    required_patient_read_scopes = ['patient/Patient.r', 'patient/Patient.rs', 'patient/Patient.read']

    permission_classes = [
        permissions.IsAuthenticated,
        ApplicationActivePermission,
        ResourcePermission,
        SearchCrosswalkPermission,
        DataAccessGrantPermission,
        TokenHasProtectedCapability,
        HasDigitalInsuranceCardScope,
    ]

    def __init__(self, version=1, **kwargs):
        super().__init__(version)

    def initial(self, request, *args, **kwargs):
        return super().initial(request, self.resource_type, *args, **kwargs)

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
