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
    """
    SLSx client class.
    See the following for more details about the endpoint usage:
    https://confluence.cms.gov/pages/viewpage.action?spaceKey=SLS&title=SLSx%3A+Client+Onboarding+Guide
    """
    redirect_uri = settings.MEDICARE_SLSX_REDIRECT_URI

    healthcheck_endpoint = settings.SLSX_HEALTH_CHECK_ENDPOINT
    token_endpoint = settings.SLSX_TOKEN_ENDPOINT
    token_endpoint_aca_token = settings.MEDICARE_SLSX_AKAMAI_ACA_TOKEN
    signout_endpoint = settings.SLSX_SIGNOUT_ENDPOINT
    userinfo_endpoint = settings.SLSX_USERINFO_ENDPOINT

    # SSL verify for internal endpoints can't currently use SSL verification (this may change in the future)
    verify_ssl_internal = settings.SLSX_VERIFY_SSL_INTERNAL
    verify_ssl_external = settings.SLSX_VERIFY_SSL_EXTERNAL

    def __init__(self):
        self.auth_token = None
        self.user_id = None
        self.signout_status_code = None
        self.token_status_code = None
        self.userinfo_status_code = None
        self.validate_signout_status_code = None
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
        """
        Common headers used for all endpoint requests
        """
        # keep using deprecated conv - no conflict issue
        headers = {"Content-Type": "application/json",
                   "Cookie": self.token_endpoint_aca_token,
                   "X-SLS-starttime": str(datetime.datetime.utcnow())}

        if request is not None:
            headers.update({"X-Request-ID": str(getattr(request, '_logging_uuid', None)
                            if hasattr(request, '_logging_uuid') else '')})
        return headers

    def exchange_for_access_token(self, req_token, request):
        """
        Exchanges the request_token from the slsx -> medicare.gov
        login flow for an auth_token via the slsx token endpoint.
        """
        data_dict = {
            "request_token": req_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        headers = self.slsx_common_headers(request)

        auth_flow_dict = get_session_auth_flow_trace(request)

        response = requests.post(self.token_endpoint,
                                 auth=self.basic_auth(),
                                 json=data_dict,
                                 headers=headers,
                                 allow_redirects=False,
                                 verify=self.verify_ssl_external,
                                 hooks={'response': [
                                        response_hook_wrapper(sender=SLSxTokenResponse,
                                                              auth_flow_dict=auth_flow_dict)]})
        self.token_status_code = response.status_code
        response.raise_for_status()

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
        """
        Retrieves and returns bene information containing MBI/HICN values
        from the userinfo endpoint.
        """
        headers = self.slsx_common_headers(request)
        headers.update(self.auth_header())

        auth_flow_dict = get_session_auth_flow_trace(request)

        response = requests.get(self.userinfo_endpoint + "/" + self.user_id,
                                headers=headers,
                                allow_redirects=False,
                                verify=self.verify_ssl_internal,
                                hooks={'response': [
                                       response_hook_wrapper(sender=SLSxUserInfoResponse,
                                                             auth_flow_dict=auth_flow_dict)]})
        self.userinfo_status_code = response.status_code
        response.raise_for_status()

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

    def service_health_check(self, request):
        """
        Checks the SLSx service health check endpoint to see if it is online.
        This is used in the mymedicare_login() view at the start of the auth flow
        and will produce an exception if not successful. This is also used by
        the BB2 /health/external check.
        """
        headers = self.slsx_common_headers(request)
        response = requests.get(self.healthcheck_endpoint,
                                headers=headers,
                                allow_redirects=False,
                                verify=self.verify_ssl_internal,
                                timeout=5)
        response.raise_for_status()
        return True

    def user_signout(self, request):
        """
        This uses the SLSx signout endpoint to sign out the bene.
        After it does the signout, the response is a redirect to the
        Medicare.gov signout page. Since this is more of a browser type
        functionality, we disable the redirects in the HTTP GET call.
        NOTE: This enpoint always returns a 302---even if the signout
              did not work.
        """
        headers = self.slsx_common_headers(request)
        headers.update(self.auth_header())

        auth_flow_dict = get_session_auth_flow_trace(request)

        response = requests.get(self.signout_endpoint,
                                headers=headers,
                                allow_redirects=False,
                                verify=self.verify_ssl_external)
        self.signout_status_code = response.status_code
        response.raise_for_status()

        if self.signout_status_code != status.HTTP_302_FOUND:
            log_authenticate_start(auth_flow_dict, "FAIL",
                                   "SLSx signout response_code = {code}."
                                   " Expecting HTTP_302_FOUND.".format(code=self.signout_status_code),
                                   slsx_client=self)
            raise BBMyMedicareSLSxSignoutException(settings.MEDICARE_ERROR_MSG)

    def validate_user_signout(self, request):
        """
        Performs a call to userinfo_endpoint to validate that the bene is
        signed out. When NOT signed out, an exception is thrown.
        This assumes the bene is signed out, if the userinfo endpoint returns
        a HTTP_403_FORBIDDEN respose and the auth_token is no longer valid.
        """
        headers = self.slsx_common_headers(request)
        headers.update(self.auth_header())

        auth_flow_dict = get_session_auth_flow_trace(request)

        response = requests.get(self.userinfo_endpoint + "/" + self.user_id,
                                headers=headers,
                                allow_redirects=False,
                                verify=self.verify_ssl_internal,
                                hooks={'response': [
                                       response_hook_wrapper(sender=SLSxUserInfoResponse,
                                                             auth_flow_dict=auth_flow_dict)]})
        self.validate_signout_status_code = response.status_code

        if self.validate_signout_status_code != status.HTTP_403_FORBIDDEN:
            log_authenticate_start(auth_flow_dict, "FAIL",
                                   "SLSx validate signout response_code = {code}."
                                   " Expecting HTTP_403_FORBIDDEN.".format(code=self.validate_signout_status_code),
                                   slsx_client=self)
            raise BBMyMedicareSLSxValidateSignoutException(settings.MEDICARE_ERROR_MSG)
