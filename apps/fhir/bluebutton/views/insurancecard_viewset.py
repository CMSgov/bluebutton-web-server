from rest_framework import permissions
from apps.fhir.bluebutton.models import Crosswalk
from apps.fhir.bluebutton.views.viewsets_base import ResourceViewSet
from apps.authorization.permissions import DataAccessGrantPermission
from apps.capabilities.permissions import TokenHasProtectedCapability
from apps.fhir.bluebutton.permissions import (
    SearchCrosswalkPermission,
    ResourcePermission,
    ApplicationActivePermission,
)

from rest_framework.response import Response


def _is_not_empty(s: set) -> bool:
    if len(s) > 0:
        return True
    else:
        return False


class HasDigitalInsuranceCardScope(permissions.BasePermission):

    required_coverage_search_scopes = ['patient/Coverage.rs', 'patient/Coverage.s', 'patient/Coverage.read']
    required_patient_read_scopes = ['patient/Patient.r', 'patient/Patient.rs', 'patient/Patient.read']

    def has_permission(self, request, view) -> bool:  # type: ignore
        # Is this an authorized request? If not, exit.
        if request.GET.get('auth', None) is None:
            return False

        # If we're authenticated, then we can check the scopes from the token.
        token_scopes = request.auth.scope
        # Two things need to be true:
        #  1. At least one of the scopes in the token needs to be one of the above coverage scopes.
        #  2. At leaset one of the scopes in the token needs to be one of the above read scopes.
        coverage_set = set(HasDigitalInsuranceCardScope.required_coverage_search_scopes)
        patient_set = set(HasDigitalInsuranceCardScope.required_patient_read_scopes)
        token_set = set(token_scopes)
        return (_is_not_empty(coverage_set.intersection(token_set))
                and _is_not_empty(patient_set.intersection(token_set)))


class DigitalInsuranceCardViewSet(ResourceViewSet):
    """Digital Insurance Card (bundle) django-rest-framework ViewSet experiment

    Args:
        FhirDataView: Base mixin, unchanged
        viewsets: django-rest-framework ViewSet base class
    """

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

    def __init__(self, version, **kwargs):
        super().__init__(version)
        self.resource_type = 'Bundle'

    def initial(self, request, *args, **kwargs):
        return super().initial(request, self.resource_type, *args, **kwargs)

    def list(self, request, resource_id, *args, **kwargs):
        return Response({"ok": "go this is the viewset"})

    def build_url(self, fhir_settings, resource_type, resource_id=None, *args, **kwargs):
        if fhir_settings.fhir_url.endswith('v1/fhir/'):
            # only if called by tests
            return f"{fhir_settings.fhir_url}{resource_type}/"
        else:
            # TODO - is this preferred (explicit), or should we keep using the implicit model APIS that Django creates?
            fhir_id = Crosswalk.objects.get(user=self.request.user).fhir_id(self.version)
            if self.version == 3 and getattr(fhir_settings, 'fhir_url_v3', None):
                fhir_url = fhir_settings.fhir_url_v3
            else:
                fhir_url = fhir_settings.fhir_url
            return f"{fhir_url}/v{self.version}/fhir/Patient/{fhir_id}/$generate-insurance-card"
