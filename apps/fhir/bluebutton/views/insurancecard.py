from waffle import switch_is_active
from apps.fhir.bluebutton.views.generic import FhirDataView
from apps.fhir.bluebutton.permissions import (SearchCrosswalkPermission,
                                              ResourcePermission,
                                              ApplicationActivePermission)
from apps.authorization.permissions import DataAccessGrantPermission
from apps.capabilities.permissions import TokenHasProtectedCapability
from django.http import JsonResponse

from rest_framework import permissions  # pyright: ignore[reportMissingImports]


def _is_not_empty(s: set) -> bool:
    if len(s) > 0:
        return True
    else:
        return False


class HasDigitalInsuranceCardScope(permissions.BasePermission):

    required_coverage_search_scopes = ['patient/Coverage.rs', 'patient/Coverage.s', 'patient/Coverage.read']
    required_patient_read_scopes = ['patient/Patient.r', 'patient/Patient.rs', 'patient/Patient.read']

    def has_permission(self, request, view) -> bool:  # type: ignore
        print("HasDigitalInsuranceCardScope has_permission")

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

        # print()
        # print("CS", coverage_set)
        # print("PS", patient_set)
        # print("TS", token_set)

        return (_is_not_empty(coverage_set.intersection(token_set))
                and _is_not_empty(patient_set.intersection(token_set)))


class WaffleSwitchV3IsActive(permissions.BasePermission):
    def has_permission(self, request, view):
        return switch_is_active('v3_endpoints')


class DigitalInsuranceCardView(FhirDataView):
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
        # return super().get(request, self.resource_type, *args, **kwargs)
        return JsonResponse(status=200, data={"ok": "go"})

    # How do the has_permission herre and the has_permission in the permission classes
    # play together? If they pass, can this fail? Visa-versa?

    def has_permission(self, request, view):
        # TODO: Why is this not being called?
        # A print statement where this comment is does not appear when unit tests are run.
        # But, the permission classes run. Where/when does has_permission get called?
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
