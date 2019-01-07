import logging
from requests import Session, Request
from rest_framework import (exceptions, permissions)
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.fhir.parsers import FHIRParser
from apps.fhir.renderers import FHIRRenderer
from apps.dot_ext.throttling import TokenRateThrottle
from apps.fhir.server import connection as backend_connection
from ..signals import (
    pre_fetch,
    post_fetch
)
from apps.authorization.permissions import DataAccessGrantPermission
from ..authentication import OAuth2ResourceOwner
from ..permissions import (HasCrosswalk, ResourcePermission)
from ..exceptions import UpstreamServerException
from ..utils import (build_fhir_response,
                     FhirServerVerify,
                     get_resourcerouter)

logger = logging.getLogger('hhs_server.%s' % __name__)


class FhirDataView(APIView):

    parser_classes = [JSONParser, FHIRParser]
    renderer_classes = [JSONRenderer, FHIRRenderer]
    throttle_classes = [TokenRateThrottle]
    authentication_classes = [OAuth2ResourceOwner]
    permission_classes = [permissions.IsAuthenticated, HasCrosswalk, ResourcePermission, DataAccessGrantPermission]

    # Must return a Crosswalk
    def check_resource_permission(self, request, **kwargs):
        raise NotImplementedError()

    def build_parameters(self, request):
        raise NotImplementedError()

    def validate_response(self, response):
        pass

    def initial(self, request, resource_type, *args, **kwargs):
        """
        Read from Remote FHIR Server
        # Example client use in curl:
        # curl -X GET http://127.0.0.1:8000/fhir/Patient/1234
        """

        logger.debug("resource_type: %s" % resource_type)
        logger.debug("Interaction: read")
        logger.debug("Request.path: %s" % request.path)

        request.resource_type = resource_type

        super(FhirDataView, self).initial(request, *args, **kwargs)

    def get(self, request, resource_type, *args, **kwargs):

        out_data = self.fetch_data(request, resource_type, *args, **kwargs)

        return Response(out_data)

    def fetch_data(self, request, resource_type, *args, **kwargs):
        resource_router = get_resourcerouter(request.crosswalk)
        target_url = self.build_url(resource_router,
                                    resource_type,
                                    *args,
                                    **kwargs)

        logger.debug('FHIR URL with key:%s' % target_url)

        get_parameters = self.build_parameters(request)

        logger.debug('Here is the URL to send, %s now add '
                     'GET parameters %s' % (target_url, get_parameters))

        # Now make the call to the backend API
        req = Request('GET',
                      target_url,
                      data=get_parameters,
                      params=get_parameters,
                      headers=backend_connection.headers(request, url=target_url))
        s = Session()
        prepped = s.prepare_request(req)
        # Send signal
        pre_fetch.send_robust(self.__class__, request=req)
        r = s.send(
            prepped,
            cert=backend_connection.certs(crosswalk=request.crosswalk),
            timeout=resource_router.wait_time,
            verify=FhirServerVerify(crosswalk=request.crosswalk))
        # Send signal
        post_fetch.send_robust(self.__class__, request=prepped, response=r)
        response = build_fhir_response(request._request, target_url, request.crosswalk, r=r, e=None)

        if response.status_code == 404:
            raise exceptions.NotFound(detail='The requested resource does not exist')

        # TODO: This should be more specific
        if response.status_code >= 300:
            raise UpstreamServerException(detail='An error occurred contacting the upstream server')

        self.validate_response(response)

        out_data = r.json()

        self.check_object_permissions(request, out_data)

        return out_data
