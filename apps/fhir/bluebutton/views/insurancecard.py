from apps.fhir.bluebutton.views.generic import FhirDataView
from apps.fhir.bluebutton.permissions import (SearchCrosswalkPermission,
                                              ResourcePermission,
                                              ApplicationActivePermission)
from apps.authorization.permissions import DataAccessGrantPermission
from apps.capabilities.permissions import TokenHasProtectedCapability

from rest_framework import permissions


class HasDigitalInsuranceCardScope(permissions.BasePermission):
    def has_permission(self, request, view):
        required_scopes = getattr(view, 'required_scopes', None)
        if required_scopes is None:
            return True

        if hasattr(request, 'auth') and request.auth is not None:
            token_scopes = request.auth.scope
            return any(scope in token_scopes for scope in required_scopes)
        return False


class DigitalInsuranceCardReadView(FhirDataView):
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

    def __init__(self, version=1):
        super().__init__(version)
        self.resource_type = 'Bundle'

    def has_permission(self, request, view):
        required_scopes = getattr(view, 'required_scopes', None)
        if required_scopes is None:
            return False
        return request.user.is_authenticated and hasattr(request.user, 'crosswalk')

    def build_parameters(self, request):
        patient_id = request.query_params.get('patient', None)
        if not patient_id:
            patient_id = request.user.crosswalk.fhir_id
        return {
            "_format": "json"
        }

    def build_url(self, resource_router, resource_type, resource_id, **kwargs):
        if resource_router.fhir_url.endswith('v1/fhir/'):
            # only if called by tests
            return "{}{}/{}/".format(resource_router.fhir_url, resource_type, resource_id)
        else:
            if self.version == 3 and resource_router.fhir_url_v3:
                fhir_url = resource_router.fhir_url_v3
            else:
                fhir_url = resource_router.fhir_url
            return f"{fhir_url}/v{self.version}/fhir/{resource_type}/{resource_id}/"
