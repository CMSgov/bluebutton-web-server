import logging
from rest_framework import permissions
from ..permissions import (ReadCrosswalkPermission, ResourcePermission)
from apps.fhir.bluebutton.views.generic import FhirDataView

logger = logging.getLogger('hhs_server.%s' % __name__)


#####################################################################
# These functions are a stepping stone to a single class based view #
#####################################################################

class ReadView(FhirDataView):
    permission_classes = [
        permissions.IsAuthenticated,
        ResourcePermission,
        ReadCrosswalkPermission,
    ]

    def build_parameters(self, *args, **kwargs):
        return {
            "_format": "json"
        }

    def build_url(self, resource_router, resource_type, resource_id, **kwargs):
        return resource_router.fhir_url + resource_type + "/" + resource_id + "/"
