from rest_framework import permissions

from apps.authorization.permissions import DataAccessGrantPermission
from apps.capabilities.permissions import TokenHasProtectedCapability
from apps.fhir.bluebutton.permissions import (
    ApplicationActivePermission,
    ResourcePermission,
    SearchCrosswalkPermission,
)
from apps.fhir.bluebutton.views.generic import FhirDataView
from apps.fhir.bluebutton.views.read import ReadView
from apps.versions import Versions


class AuditEventView(FhirDataView):
    """Audit Event view for handling BFD Endpoint"""

    permission_classes = [
        permissions.IsAuthenticated,
        ApplicationActivePermission,
        ResourcePermission,
        SearchCrosswalkPermission,
        DataAccessGrantPermission,
        TokenHasProtectedCapability,
    ]

    def __init__(self, version=Versions.V3):
        super().__init__(version)
        self.resource_type = 'AuditEvent'

    def initial(self, request, *args, **kwargs):
        return super().initial(request, self.resource_type, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return super().get(request, self.resource_type, *args, **kwargs)

    def get_full_path(self):
        return f'/v{self.version}/fhir/AuditEvent/'

    def build_parameters(self, request):
        return {
            '_format': 'application/fhir+json',
            'entity': request.crosswalk.fhir_id(self.version),
        }

    def build_url(self, fhir_settings, resource_type, resource_id=None, *args, **kwargs):
        if self.version == Versions.V3 and getattr(fhir_settings, 'fhir_url_v3', None):
            fhir_url = fhir_settings.fhir_url_v3
        else:
            fhir_url = fhir_settings.fhir_url

        return f'{fhir_url}/v{self.version}/fhir/AuditEvent'


class ReadViewAuditEventView(ReadView):
    # Class used for AuditEvent resource
    def __init__(self, version=1):
        super().__init__(version)
        self.resource_type = 'AuditEvent'
