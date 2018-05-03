import requests
import logging
from django.utils.decorators import method_decorator
from rest_framework import exceptions
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.fhir.parsers import FHIRParser
from apps.fhir.renderers import FHIRRenderer
from apps.dot_ext.throttling import TokenRateThrottle
from apps.fhir.server import connection as backend_connection
from ..constants import ALLOWED_RESOURCE_TYPES
from ..exceptions import UpstreamServerException
from ..serializers import localize
from ..decorators import require_valid_token
from ..utils import (build_fhir_response,
                     FhirServerVerify,
                     FhirServerAuth,
                     get_resourcerouter)

logger = logging.getLogger('hhs_server.%s' % __name__)


class FhirDataView(APIView):

    parser_classes = [JSONParser, FHIRParser]
    renderer_classes = [JSONRenderer, FHIRRenderer]
    throttle_classes = [TokenRateThrottle]

    resource_type = None

    # Must return a Crosswalk
    def check_resource_permission(self, request, **kwargs):
        raise NotImplementedError()

    def build_parameters(self):
        raise NotImplementedError()

    def validate_response(self, response):
        pass

    @method_decorator(require_valid_token())
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def initial(self, request, resource_type, *args, **kwargs):
        """
        Read from Remote FHIR Server
        # Example client use in curl:
        # curl -X GET http://127.0.0.1:8000/fhir/Patient/1234
        """

        logger.debug("resource_type: %s" % resource_type)
        logger.debug("Interaction: read")
        logger.debug("Request.path: %s" % request.path)

        super().initial(request, *args, **kwargs)

        if resource_type not in ALLOWED_RESOURCE_TYPES:
            logger.info('User requested read access to the %s resource type' % resource_type)
            raise exceptions.NotFound('The requested resource type, %s, is not supported' % resource_type)

        self.crosswalk = self.check_resource_permission(request, resource_type, *args, **kwargs)
        if self.crosswalk is None:
            raise exceptions.PermissionDenied(
                'No access information was found for the authenticated user')
        if self.crosswalk.fhir_id == "":
            auth_state = FhirServerAuth(None)
            certs = (auth_state['cert_file'], auth_state['key_file'])

            # URL for patient ID.
            url = get_resourcerouter().fhir_url + \
                "Patient/?identifier=http%3A%2F%2Fbluebutton.cms.hhs.gov%2Fidentifier%23hicnHash%7C" + \
                self.crosswalk.user_id_hash + \
                "&_format=json"
            response = requests.get(url, cert=certs, verify=False)
            backend_data = response.json()

            if 'entry' in backend_data and backend_data['total'] == 1:
                fhir_id = backend_data['entry'][0]['resource']['id']
                self.crosswalk.fhir_id = fhir_id
                self.crosswalk.save()

                logger.info("Success:Beneficiary connected to FHIR")
                # Recheck perms
                self.crosswalk = self.check_resource_permission(request, resource_type, *args, **kwargs)
            else:
                raise exceptions.NotFound("The requested Beneficiary has no entry, however this may change")

        self.resource_type = resource_type

    def get(self, request, resource_type, *args, **kwargs):

        out_data = self.fetch_data(request, resource_type, *args, **kwargs)

        return Response(out_data)

    def fetch_data(self, request, resource_type, *args, **kwargs):
        resource_router = get_resourcerouter(self.crosswalk)
        target_url = self.build_url(resource_router,
                                    resource_type,
                                    *args,
                                    **kwargs)

        logger.debug('FHIR URL with key:%s' % target_url)

        get_parameters = self.build_parameters()

        logger.debug('Here is the URL to send, %s now add '
                     'GET parameters %s' % (target_url, get_parameters))

        # Now make the call to the backend API
        r = requests.get(target_url,
                         params=get_parameters,
                         cert=backend_connection.certs(crosswalk=self.crosswalk),
                         headers=backend_connection.headers(request, url=target_url),
                         timeout=resource_router.wait_time,
                         verify=FhirServerVerify(crosswalk=self.crosswalk))
        response = build_fhir_response(request._request, target_url, self.crosswalk, r=r, e=None)

        if response.status_code == 404:
            raise exceptions.NotFound(detail='The requested resource does not exist')

        # TODO: This should be more specific
        if response.status_code >= 300:
            raise UpstreamServerException(detail='An error occurred contacting the upstream server')

        self.validate_response(response)

        out_data = localize(request=request,
                            response=response,
                            crosswalk=self.crosswalk,
                            resource_type=resource_type)
        return out_data
