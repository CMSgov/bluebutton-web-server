from rest_framework import permissions
from rest_framework.response import Response

from apps.authorization.permissions import DataAccessGrantPermission
from apps.capabilities.permissions import TokenHasProtectedCapability
from ..permissions import (ReadCrosswalkPermission, ResourcePermission, ApplicationActivePermission)
from apps.fhir.bluebutton.views.generic import FhirDataView
from apps.fhir.bluebutton.views.home import get_response_json


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
            return "{}/{}/fhir/{}/{}/".format(resource_router.fhir_url, 'v2' if self.version == 2 else 'v1',
                                              resource_type, resource_id)


class ReadViewPatient(ReadView):
    # Class used for Patient resource
    def __init__(self, version=1):
        super().__init__(version)
        self.resource_type = "Patient"

    def get(self, request, *args, **kwargs):
        return_c4dic = True
        if return_c4dic:
            return Response(get_response_json("c4dic-patient-read"))
        else:
            return super().get(request, *args, **kwargs)


class ReadViewCoverage(ReadView):
    # Class used for Patient resource
    def __init__(self, version=1):
        super().__init__(version)
        self.resource_type = "Coverage"

    def get(self, request, *args, **kwargs):
        profile = request.query_params.get('_profile', '')
        if profile == "http://hl7.org/fhir/us/insurance-card/StructureDefinition/C4DIC-Coverage":
            return Response(get_response_json("c4dic-coverage-read"))
        else:
            return super().get(request, *args, **kwargs)


class ReadViewExplanationOfBenefit(ReadView):
    # Class used for Patient resource
    def __init__(self, version=1):
        super().__init__(version)
        self.resource_type = "ExplanationOfBenefit"
