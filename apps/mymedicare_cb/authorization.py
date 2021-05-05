import logging
import requests
import datetime

from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import APIException

from apps.dot_ext.loggers import get_session_auth_flow_trace
from apps.logging.serializers import SLSxTokenResponse, SLSxUserInfoResponse

from .loggers import log_authenticate_start
from .signals import response_hook_wrapper

logger = logging.getLogger('hhs_server.%s' % __name__)


class BBMyMedicareSLSxSignoutException(APIException):
    # BB2-544 custom exception
    status_code = status.HTTP_502_BAD_GATEWAY


class BBMyMedicareSLSxTokenException(APIException):
    # BB2-391 custom exception
    status_code = status.HTTP_502_BAD_GATEWAY


class BBMyMedicareSLSxUserinfoException(APIException):
    # BB2-391 custom exception
    status_code = status.HTTP_502_BAD_GATEWAY


class BBMyMedicareSLSxValidateSignoutException(APIException):
    # BB2-544 custom exception
    status_code = status.HTTP_502_BAD_GATEWAY


class BBSLSxHealthCheckFailedException(APIException):
    # BB2-391 custom exception
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class OAuth2ConfigSLSx(object):
    token_endpoint = settings.SLSX_TOKEN_ENDPOINT
    token_endpoint_aca_token = settings.MEDICARE_SLSX_AKAMAI_ACA_TOKEN
    redirect_uri = settings.MEDICARE_SLSX_REDIRECT_URI
    signout_endpoint = settings.SLSX_SIGNOUT_ENDPOINT
    userinfo_endpoint = settings.SLSX_USERINFO_ENDPOINT
    healthcheck_endpoint = settings.SLSX_HEALTH_CHECK_ENDPOINT
    verify_ssl = getattr(settings, 'SLSX_VERIFY_SSL', False)

    def __init__(self):
        self.auth_token = None
        self.user_id = None
        self.healthcheck_status_code = None
        self.healthcheck_status_mesg = None
        self.signout_status_code = None
        self.signout_status_mesg = None
        self.token_status_code = None
        self.token_status_mesg = None
        self.userinfo_status_code = None
        self.userinfo_status_mesg = None
        self.validate_signout_status_code = None
        self.validate_signout_status_mesg = None
        super().__init__()

    @property
    def client_id(self):
        return getattr(settings, 'SLSX_CLIENT_ID', False)

    @property
    def client_secret(self):
        return getattr(settings, 'SLSX_CLIENT_SECRET', False)

    def basic_auth(self):
        if self.client_id and self.client_secret:
            return (self.client_id, self.client_secret)
        return None

    def slsx_common_headers(self, request):
        # keep using deprecated conv - no conflict issue
        headers = {"Content-Type": "application/json",
                   "Cookie": self.token_endpoint_aca_token,
                   "X-SLS-starttime": str(datetime.datetime.utcnow())}

        if request is not None:
            headers.update({"X-Request-ID": str(getattr(request, '_logging_uuid', None)
                            if hasattr(request, '_logging_uuid') else '')})
        return headers

    def exchange_for_access_token(self, req_token, request):
        data_dict = {
            "request_token": req_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        headers = self.slsx_common_headers(request)

        auth_flow_dict = get_session_auth_flow_trace(request)

        try:
            response = requests.post(
                self.token_endpoint,
                auth=self.basic_auth(),
                json=data_dict,
                headers=headers,
                allow_redirects=False,
                verify=self.verify_ssl,
                hooks={
                    'response': [
                        response_hook_wrapper(sender=SLSxTokenResponse,
                                              auth_flow_dict=auth_flow_dict)]})
            self.token_status_code = response.status_code
            response.raise_for_status()
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
            self.token_status_mesg = e
            log_authenticate_start(auth_flow_dict, "FAIL",
                                   "SLSx token response error {reason}".format(reason=e),
                                   slsx_client=self)
            raise BBMyMedicareSLSxTokenException(settings.MEDICARE_ERROR_MSG)

        token_response = response.json()

        self.auth_token = token_response.get('auth_token', None)
        if self.auth_token is None:
            log_authenticate_start(auth_flow_dict, "FAIL",
                                   "Exchange auth_token is missing in response error",
                                   slsx_client=self)
            raise BBMyMedicareSLSxTokenException(settings.MEDICARE_ERROR_MSG)

        self.user_id = token_response.get('user_id', None)
        if self.user_id is None:
            log_authenticate_start(auth_flow_dict, "FAIL",
                                   "Exchange user_id is missing in response error",
                                   slsx_client=self)
            raise BBMyMedicareSLSxTokenException(settings.MEDICARE_ERROR_MSG)

        if self.user_id is None:
            log_authenticate_start(auth_flow_dict, "FAIL",
                                   "Exchange user_id is missing in response error",
                                   slsx_client=self)
            raise BBMyMedicareSLSxTokenException(settings.MEDICARE_ERROR_MSG)

    def auth_header(self):
        return {"Authorization": "Bearer %s" % (self.auth_token)}

    def get_user_info(self, request):
        headers = self.slsx_common_headers(request)
        headers.update(self.auth_header())

        auth_flow_dict = get_session_auth_flow_trace(request)

        try:
            response = requests.get(self.userinfo_endpoint + "/" + self.user_id,
                                    headers=headers,
                                    allow_redirects=False,
                                    verify=self.verify_ssl,
                                    hooks={
                                        'response': [
                                            response_hook_wrapper(sender=SLSxUserInfoResponse,
                                                                  auth_flow_dict=auth_flow_dict)]})
            self.userinfo_status_code = response.status_code
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            self.userinfo_status_mesg = e
            log_authenticate_start(auth_flow_dict, "FAIL",
                                   "SLSx userinfo response error {reason}".format(reason=e),
                                   slsx_client=self)
            raise BBMyMedicareSLSxUserinfoException(settings.MEDICARE_ERROR_MSG)

        # Get data.user part of response
        try:
            data_user_response = response.json().get('data').get('user')
        except KeyError:
            log_authenticate_start(auth_flow_dict, "FAIL",
                                   "SLSx userinfo issue with data.user sub fields in response error",
                                   slsx_client=self)
            raise BBMyMedicareSLSxUserinfoException(settings.MEDICARE_ERROR_MSG)

        if data_user_response.get('id', None) is None:
            log_authenticate_start(auth_flow_dict, "FAIL",
                                   "SLSx userinfo user_id is missing in response error",
                                   slsx_client=self)
            raise BBMyMedicareSLSxUserinfoException(settings.MEDICARE_ERROR_MSG)

        if self.user_id != data_user_response.get('id', None):
            log_authenticate_start(auth_flow_dict, "FAIL",
                                   "SLSx userinfo user_id is not equal in response error",
                                   slsx_client=self)
            raise BBMyMedicareSLSxUserinfoException(settings.MEDICARE_ERROR_MSG)

        return data_user_response

    def service_health_check(self, request, called_from_health_external=False):
        headers = self.slsx_common_headers(request)

        auth_flow_dict = get_session_auth_flow_trace(request)

        try:
            response = requests.get(self.healthcheck_endpoint,
                                    headers=headers,
                                    allow_redirects=False,
                                    verify=self.verify_ssl)
            self.healthcheck_status_code = response.status_code
            response.raise_for_status()
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
            if not called_from_health_external:
                self.healthcheck_status_mesg = e
                log_authenticate_start(auth_flow_dict, "FAIL",
                                       "SLSx service health check error {reason}".format(reason=e),
                                       slsx_client=self)
            raise BBSLSxHealthCheckFailedException(settings.MEDICARE_ERROR_MSG)

    def user_signout(self, request):
        headers = self.slsx_common_headers(request)
        headers.update(self.auth_header())

        auth_flow_dict = get_session_auth_flow_trace(request)

        try:
            response = requests.get(self.signout_endpoint,
                                    headers=headers,
                                    allow_redirects=False,
                                    verify=self.verify_ssl)
            self.signout_status_code = response.status_code
            if self.signout_status_code != status.HTTP_302_FOUND:
                log_authenticate_start(auth_flow_dict, "FAIL",
                                       "SLSx signout response_code = {code}."
                                       " Expecting HTTP_302_FOUND.".format(code=self.signout_status_code),
                                       slsx_client=self)
                raise BBMyMedicareSLSxSignoutException(settings.MEDICARE_ERROR_MSG)
            response.raise_for_status()
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
            if self.signout_status_code != status.HTTP_302_FOUND:
                self.signout_status_mesg = e
                log_authenticate_start(auth_flow_dict, "FAIL",
                                       "SLSx signout error {reason}".format(reason=e),
                                       slsx_client=self)
                raise BBMyMedicareSLSxSignoutException(settings.MEDICARE_ERROR_MSG)

    def validate_user_signout(self, request):
        """
        Performs a call to self.get_user_info to validate that the bene is
        signed out. When NOT signed out, an exception is thrown.
        This assumes the bene is signed out, if the userinfo endpoint returns
        a HTTP_403_FORBIDDEN respose, since the auth_token is no longer valid.
        """
        headers = self.slsx_common_headers(request)
        headers.update(self.auth_header())

        auth_flow_dict = get_session_auth_flow_trace(request)

        try:
            response = requests.get(self.userinfo_endpoint + "/" + self.user_id,
                                    headers=headers,
                                    allow_redirects=False,
                                    verify=self.verify_ssl,
                                    hooks={
                                        'response': [
                                            response_hook_wrapper(sender=SLSxUserInfoResponse,
                                                                  auth_flow_dict=auth_flow_dict)]})
            self.validate_signout_status_code = response.status_code
            if self.validate_signout_status_code != status.HTTP_403_FORBIDDEN:
                log_authenticate_start(auth_flow_dict, "FAIL",
                                       "SLSx validate signout response_code = {code}."
                                       " Expecting HTTP_403_FORBIDDEN.".format(code=self.validate_signout_status_code),
                                       slsx_client=self)
                raise BBMyMedicareSLSxValidateSignoutException(settings.MEDICARE_ERROR_MSG)
            response.raise_for_status()
        except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
            if self.validate_signout_status_code != status.HTTP_403_FORBIDDEN:
                self.validate_signout_status_mesg = e
                log_authenticate_start(auth_flow_dict, "FAIL",
                                       "SLSx validate signout error {reason}".format(reason=e),
                                       slsx_client=self)
                raise BBMyMedicareSLSxValidateSignoutException(settings.MEDICARE_ERROR_MSG)
