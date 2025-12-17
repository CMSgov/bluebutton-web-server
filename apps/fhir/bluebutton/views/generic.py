import hashlib

import voluptuous
import logging

from apps.versions import VersionNotMatched, Versions
import apps.logging.request_logger as bb2logging

from django.core.exceptions import ObjectDoesNotExist, BadRequest
from oauth2_provider.models import AccessToken
from requests import Session, Request
from rest_framework import (exceptions, permissions)
from rest_framework.exceptions import NotFound
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from urllib.parse import quote

from apps.authorization.permissions import DataAccessGrantPermission
from apps.dot_ext.throttling import TokenRateThrottle
from apps.fhir.parsers import FHIRParser
from apps.fhir.renderers import FHIRRenderer
from apps.fhir.server.settings import fhir_settings
from apps.fhir.server import connection as backend_connection
from apps.fhir.bluebutton.authentication import OAuth2ResourceOwner
from apps.fhir.bluebutton.exceptions import process_error_response
from apps.fhir.bluebutton.permissions import (HasCrosswalk, ResourcePermission, ApplicationActivePermission)
from apps.fhir.bluebutton.signals import (
    pre_fetch,
    post_fetch
)
from apps.fhir.bluebutton.utils import (
    FhirServerAuth,
    build_fhir_response,
    valid_patient_read_or_search_call,
    validate_query_parameters
)

logger = logging.getLogger(bb2logging.HHS_SERVER_LOGNAME_FMT.format(__name__))


class FhirDataView(APIView):
    version = 1
    parser_classes = [JSONParser, FHIRParser]
    renderer_classes = [JSONRenderer, FHIRRenderer]
    throttle_classes = [TokenRateThrottle]
    authentication_classes = [OAuth2ResourceOwner]
    # BB2-149 note, check authenticated first, then app active etc.
    permission_classes = [
        permissions.IsAuthenticated,
        ApplicationActivePermission,
        HasCrosswalk,
        ResourcePermission,
        DataAccessGrantPermission
    ]

    def __init__(self, version=1):
        self.version = version
        super().__init__()

    # Must return a Crosswalk
    def check_resource_permission(self, request, **kwargs):
        raise NotImplementedError()

    def build_parameters(self, request):
        raise NotImplementedError()

    def build_url(self, resource_router, resource_type, resource_id, **kwargs):
        raise NotImplementedError()

    def map_parameters(self, params):
        transforms = getattr(self, 'QUERY_TRANSFORMS', {})
        for key, correct in transforms.items():
            val = params.pop(key, None)
            if val is not None:
                params[correct] = val
        return params

    def filter_parameters(self, request):
        params = self.map_parameters(request.query_params.dict())
        # Get list from _lastUpdated QueryDict(), since it can have multi params
        params['_lastUpdated'] = request.query_params.getlist('_lastUpdated')

        schema = voluptuous.Schema(
            getattr(self, 'QUERY_SCHEMA', {}),
            extra=voluptuous.REMOVE_EXTRA)
        return schema(params)

    def initial(self, request, resource_type, *args, **kwargs):
        """
        Read from Remote FHIR Server
        # Example client use in curl:
        # curl -X GET http://127.0.0.1:8000/fhir/Patient/1234
        """

        logger.debug('resource_type: %s' % resource_type)
        logger.debug('Interaction: read')
        logger.debug('Request.path: %s' % request.path)
        req_meta = request.META

        if 'HTTP_AUTHORIZATION' in req_meta:
            access_token = req_meta['HTTP_AUTHORIZATION'].split(' ')[1]
            try:
                at = AccessToken.objects.get(token=access_token)
                log_message = {
                    'name': 'FHIR Endpoint AT Logging',
                    'access_token_id': at.id,
                    'access_token_application_id': at.application.id,
                    'access_token_hash': {hashlib.sha256(str(access_token).encode('utf-8')).hexdigest()},
                    'access_token_username': at.user.username,
                }
                logger.info(log_message)
            except ObjectDoesNotExist:
                pass

        request.resource_type = resource_type

        super(FhirDataView, self).initial(request, *args, **kwargs)

    def get(self, request, resource_type, *args, **kwargs):

        out_data = self.fetch_data(request, resource_type, *args, **kwargs)

        return Response(out_data)

    def fetch_data(self, request, resource_type, *args, **kwargs):
        target_url = self.build_url(fhir_settings,
                                    resource_type,
                                    *args, **kwargs)

        logger.debug('FHIR URL with key:%s' % target_url)

        try:
            get_parameters = {**self.filter_parameters(request), **self.build_parameters(request)}
        except voluptuous.error.Invalid as e:
            raise exceptions.ParseError(detail=e.msg)

        logger.debug('Here is the URL to send, %s now add '
                     'GET parameters %s' % (target_url, get_parameters))
        request.session.version = self.version

        # Now make the call to the backend API
        req = Request('GET',
                      target_url,
                      params=get_parameters,
                      headers=backend_connection.headers(request, url=target_url))
        s = Session()

        # BB2-1544 request header url encode if header value (app name) contains char (>256)
        if req.headers.get('BlueButton-Application') is not None:
            try:
                req.headers.get('BlueButton-Application').encode('latin1')
            except UnicodeEncodeError:
                req.headers['BlueButton-Application'] = quote(req.headers.get('BlueButton-Application'))

        prepped = s.prepare_request(req)
        query_param = prepped.headers.get('BlueButton-OriginalQuery')

        if query_param:
            accepted_query_parameters = getattr(self, 'QUERY_SCHEMA', {})
            validation_result = validate_query_parameters(accepted_query_parameters, query_param)
            if not validation_result.valid:
                error = BadRequest(
                    f'Bad request, invalid query parameters were passed: {validation_result.invalid_params}'
                )
                raise error

        if resource_type == 'Patient':

            resource_id = kwargs.get('resource_id')
            beneficiary_id = prepped.headers.get('BlueButton-BeneficiaryId')

            # For patient read and search calls, we need to ensure that what is being passed, either in
            # query parameters for search calls, or in the resource_id for read calls, is valid for the
            # current session (matching the beneficiary_id). If not, raise a 404 Not found before calling BFD.
            if not valid_patient_read_or_search_call(beneficiary_id, resource_id, query_param):
                error = NotFound('Not found.')
                raise error

            # Handle the case where it is a patient search call, but neither _id or identifier were passed
            if '_id' not in get_parameters.keys() and 'identifier' not in get_parameters.keys():
                get_parameters['_id'] = request.crosswalk.fhir_id(self.version)
                # Reset the request parameters and the prepped request after adding the missing, but required, _id param
                req.params = get_parameters
                prepped = s.prepare_request(req)

        match self.version:
            case Versions.V1:
                api_ver_str = 'v1'
            case Versions.V2:
                api_ver_str = 'v2'
            case Versions.V3:
                api_ver_str = 'v3'
            case _:
                raise VersionNotMatched(f'{self.version} is not a valid version constant')

        # Send signal
        fhir_server_auth = FhirServerAuth()
        pre_fetch.send_robust(FhirDataView, request=req, auth_request=request, api_ver=api_ver_str)
        r = s.send(
            prepped,
            cert=(fhir_server_auth['cert_file'], fhir_server_auth['key_file']),
            timeout=fhir_settings.wait_time,
            verify=fhir_settings.verify_server
        )
        # Send signal
        post_fetch.send_robust(FhirDataView, request=prepped, auth_request=request, response=r, api_ver=api_ver_str)
        response = build_fhir_response(request._request, target_url, request.crosswalk, r=r, e=None)

        # BB2-128
        error = process_error_response(response)
        if error is not None:
            raise error

        out_data = r.json()

        self.check_object_permissions(request, out_data)

        return out_data
