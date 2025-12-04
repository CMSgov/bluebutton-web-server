from apps.fhir.bluebutton.views.generic import FhirDataView
from apps.fhir.bluebutton.permissions import (SearchCrosswalkPermission,
                                              ResourcePermission,
                                              ApplicationActivePermission)
from apps.authorization.permissions import DataAccessGrantPermission
# FIXME: removed for local testing
# from apps.capabilities.permissions import TokenHasProtectedCapability
from django.http import JsonResponse

from rest_framework import permissions  # pyright: ignore[reportMissingImports]

from apps.versions import noisy_has_permission


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

        print()
        print("CS", coverage_set)
        print("PS", patient_set)
        print("TS", token_set)

        return (_is_not_empty(coverage_set.intersection(token_set))
                and _is_not_empty(patient_set.intersection(token_set)))


class DigitalInsuranceCardView(FhirDataView):
    '''Digital Insurance Card view for handling BFD Endpoint'''

    permission_classes = [
        permissions.IsAuthenticated,
        noisy_has_permission(ApplicationActivePermission),
        noisy_has_permission(ResourcePermission),
        noisy_has_permission(SearchCrosswalkPermission),
        noisy_has_permission(DataAccessGrantPermission),
        # noisy_has_permission(TokenHasProtectedCapability),
        noisy_has_permission(HasDigitalInsuranceCardScope),
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
        print("GET OF INSURANCE CARD")
        print("request: ", request.__dict__)
        print("self.resource_type: ", self.resource_type)
        # return super().get(request, self.resource_type, *args, **kwargs)
        return JsonResponse(status=200, data={"ok": "go"})

    # How do the has_permission herre and the has_permission in the permission classes
    # play together? If they pass, can this fail? Visa-versa?
    # def has_permission(self, request, view) -> bool:  # type: ignore
    #     required_scopes = getattr(view, 'required_scopes', None)
    #     if required_scopes is None:
    #         return True

    #     if hasattr(request, 'auth') and request.auth is not None:
    #         token_scopes = request.auth.scope
    #         return any(scope in token_scopes for scope in required_scopes)
    #     return False

    def has_permission(self, request, view):
        # TODO: Why is this not being called?
        # A print statement where this comment is does not appear when unit tests are run.
        # But, the permission classes run. Where/when does has_permission get called?
        # required_scopes = getattr(view, 'required_scopes', None)
        # if required_scopes is None:
        #     return False
        # return request.user.is_authenticated and hasattr(request.user, 'crosswalk')
        print("HAS_PERMISSION IN DIGITALINSURANCECARD")
        return True

    def build_parameters(self, request):
        print("BUILD_PARAMETERS IN DIGITALINSURANCECARD")
        return {
            '_format': 'application/fhir+json'
        }

    def build_url(self, fhir_settings, resource_type, resource_id=None, *args, **kwargs):
        print("BUILD_URL IN DIGITALINSURANCECARD")
        if fhir_settings.fhir_url.endswith('v1/fhir/'):
            # only if called by tests
            return f"{fhir_settings.fhir_url}{resource_type}/"
        else:
            if self.version == 3 and getattr(fhir_settings, 'fhir_url_v3', None):
                fhir_url = fhir_settings.fhir_url_v3
            else:
                fhir_url = fhir_settings.fhir_url
            return f"{fhir_url}/v{self.version}/fhir/Patient/{resource_id}/$generate-insurance-card"
