from rest_framework import permissions

from apps.authorization.permissions import DataAccessGrantPermission
from apps.capabilities.permissions import TokenHasProtectedCapability
from ..permissions import (ReadCrosswalkPermission, ResourcePermission, ApplicationActivePermission)
from apps.fhir.bluebutton.views.generic import FhirDataView


#####################################################################
# These functions are a stepping stone to a single class based view #
#####################################################################

class ReadView(FhirDataView):
    # Base class for FHIR resource read views

    # BB2-149 note, check authenticated first, then app active etc.
    permission_classes = [
        permissions.IsAuthenticated,
        ApplicationActivePermission,
        ResourcePermission,
        ReadCrosswalkPermission,
        DataAccessGrantPermission,
        TokenHasProtectedCapability,
    ]

    def __init__(self, version=1):
        self.resource_type = None
        super().__init__(version)

    def initial(self, request, *args, **kwargs):
        return super().initial(request, self.resource_type, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return super().get(request, self.resource_type, *args, **kwargs)

    def build_parameters(self, *args, **kwargs):
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


class ReadViewPatient(ReadView):
    # Class used for Patient resource
    def __init__(self, version=1):
        super().__init__(version)
        self.resource_type = "Patient"


class ReadViewCoverage(ReadView):
    # Class used for Patient resource
    def __init__(self, version=1):
        super().__init__(version)
        self.resource_type = "Coverage"


class ReadViewExplanationOfBenefit(ReadView):
    # Class used for Patient resource
    def __init__(self, version=1):
        super().__init__(version)
        self.resource_type = "ExplanationOfBenefit"
