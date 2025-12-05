from apps.fhir.bluebutton.views.generic import FhirDataView
from apps.fhir.bluebutton.permissions import (SearchCrosswalkPermission,
                                              ResourcePermission,
                                              ApplicationActivePermission)
from apps.authorization.permissions import DataAccessGrantPermission
from apps.fhir.bluebutton.models import Crosswalk

from rest_framework import permissions  # pyright: ignore[reportMissingImports]


class HasDigitalInsuranceCardScope(permissions.BasePermission):

    required_coverage_search_scopes = ['patient/Coverage.rs', 'patient/Coverage.s', 'patient/Coverage.read']
    required_patient_read_scopes = ['patient/Patient.r', 'patient/Patient.rs', 'patient/Patient.read']

    def _is_not_empty(s: set) -> bool:
        return len(s) > 0

    def has_permission(self, request, view) -> bool:  # type: ignore
        # Is this an authorized request? If not, exit.
        if not hasattr(request, 'auth'):
            return False
        if request.auth is None:
            return False

        # If we're authenticated, then we can check the scopes from the token.
        token_scope_string = request.auth.scope
        # This will be a space-separated string.
        token_scopes = list(map(lambda s: s.strip(), token_scope_string.split(" ")))

        # Two things need to be true:
        #  1. At least one of the scopes in the token needs to be one of the above coverage scopes.
        #  2. At leaset one of the scopes in the token needs to be one of the above read scopes.
        coverage_set = set(HasDigitalInsuranceCardScope.required_coverage_search_scopes)
        patient_set = set(HasDigitalInsuranceCardScope.required_patient_read_scopes)
        token_set = set(token_scopes)

        return (HasDigitalInsuranceCardScope._is_not_empty(coverage_set.intersection(token_set))
                and HasDigitalInsuranceCardScope._is_not_empty(patient_set.intersection(token_set)))


class DigitalInsuranceCardView(FhirDataView):
    '''Digital Insurance Card view for handling BFD Endpoint'''

    permission_classes = [
        permissions.IsAuthenticated,
        ApplicationActivePermission,
        ResourcePermission,
        SearchCrosswalkPermission,
        DataAccessGrantPermission,
        # 20251205: We are bypassing ProtectedCapabilities at this time because
        # the existing capability model has no notion of multiple capabilities for a single
        # endpoint. In the case of C4DIC, the permission check HasDigitalInsuranceCardScope
        # handles the set checks that are required for this particular API call.
        # TokenHasProtectedCapability
        HasDigitalInsuranceCardScope,
    ]

    # FIXME: Are these required here? Or, can I put them in the permission class?
    # required_coverage_search_scopes = ['patient/Coverage.rs', 'patient/Coverage.s', 'patient/Coverage.read']
    # required_patient_read_scopes = ['patient/Patient.r', 'patient/Patient.rs', 'patient/Patient.read']

    # TODO/FIXME: What are the version=1? doing? Check/look into.
    def __init__(self, version=1):
        super().__init__(version)
        self.resource_type = 'Bundle'

    def initial(self, request, *args, **kwargs):
        return super().initial(request, self.resource_type, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return super().get(request, self.resource_type, *args, **kwargs)
        # return JsonResponse(status=200, data={"consternation": "vorciferous"})

    def get_full_path(self):
        return f"/{DigitalInsuranceCardView.version}/fhir/DigitalInsuranceCard"

    def build_parameters(self, request):
        return {
            '_format': 'application/fhir+json'
        }

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
