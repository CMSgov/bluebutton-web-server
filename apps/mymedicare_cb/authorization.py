import requests
import datetime

import apps.logging.request_logger as logging

from django.conf import settings
from django.core.exceptions import ValidationError
from enum import Enum
from rest_framework import status
from rest_framework.exceptions import APIException

from apps.fhir.bluebutton.models import hash_hicn, hash_mbi
from apps.logging.serializers import SLSxTokenResponse, SLSxUserInfoResponse

from .signals import response_hook_wrapper
from .validators import is_mbi_format_valid, is_mbi_format_synthetic


MSG_SLS_RESP_MISSING_AUTHTOKEN = "Exchange auth_token is missing in response error"
MSG_SLS_RESP_MISSING_USERID = "Exchange user_id is missing in response error"
MSG_SLS_RESP_MISSING_USERINFO_USERID = (
    "SLSx userinfo user_id is missing in response error"
)
MSG_SLS_RESP_NOT_MATCHED_USERINFO_USERID = (
    "SLSx userinfo user_id is not equal in response error"
)


class MedicareCallbackExceptionType(Enum):
    TOKEN = 1
    USERINFO = 2
    SIGNOUT = 3
    VALIDATE_SIGNOUT = 4
    VALIDATION_ERROR = 5
    AUTHN_USERINFO = 6
    CALLBACK_CW_CREATE = 7
    CALLBACK_CW_UPDATE = 8


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


class BBMyMedicareCallbackAuthenticateSlsUserInfoValidateException(APIException):
    # BB2-237 custom exception
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


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

    def __init__(self, args_dict=None):
        # args_dict added for legacy tests adaption
        self.auth_token = None
        self.user_id = args_dict.get("username", None) if args_dict else None
        self.signout_status_code = None
        self.token_status_code = None
        self.userinfo_status_code = None
        self.validate_signout_status_code = None
        self.mbi = None
        self.mbi_hash = args_dict.get("user_mbi_hash", None) if args_dict else None
        self.hicn = None
        self.hicn_hash = args_dict.get("user_hicn_hash", None) if args_dict else None
        self.mbi_format_valid = None
        self.mbi_format_synthetic = None
        self.mbi_format_msg = None
        self.firstname = args_dict.get("first_name", "") if args_dict else ""
        self.lastname = args_dict.get("last_name", "") if args_dict else ""
        self.email = args_dict.get("email", "") if args_dict else ""
        super().__init__()

    @property
    def client_id(self):
        return getattr(settings, "SLSX_CLIENT_ID", False)

    @property
    def client_secret(self):
        return getattr(settings, "SLSX_CLIENT_SECRET", False)

    def basic_auth(self):
        if self.client_id and self.client_secret:
            return (self.client_id, self.client_secret)
        return None

    def slsx_common_headers(self, request):
        """
        Common headers used for all endpoint requests
        """
        # keep using deprecated conv - no conflict issue
        headers = {
            "Content-Type": "application/json",
            "Cookie": self.token_endpoint_aca_token,
            "X-SLS-starttime": str(datetime.datetime.utcnow()),
        }

        if request is not None:
            headers.update(
                {
                    "X-Request-ID": str(
                        getattr(request, "_logging_uuid", None)
                        if hasattr(request, "_logging_uuid")
                        else ""
                    )
                }
            )
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

        response = requests.post(
            self.token_endpoint,
            auth=self.basic_auth(),
            json=data_dict,
            headers=headers,
            allow_redirects=False,
            verify=self.verify_ssl_external,
            hooks={
                "response": [
                    response_hook_wrapper(sender=SLSxTokenResponse, request=request)
                ]
            },
        )
        self.token_status_code = response.status_code
        response.raise_for_status()

        token_response = response.json()

        self.auth_token = token_response.get("auth_token", None)
        self.user_id = token_response.get("user_id", None)

        self.validate_asserts(
            request,
            [
                (self.auth_token is None, MSG_SLS_RESP_MISSING_AUTHTOKEN),
                (self.user_id is None, MSG_SLS_RESP_MISSING_USERID),
            ],
            MedicareCallbackExceptionType.TOKEN,
        )

    def auth_header(self):
        return {"Authorization": "Bearer %s" % (self.auth_token)}

    def get_user_info(self, request):
        """
        Retrieves and returns bene information containing MBI/HICN values
        from the userinfo endpoint.
        """
        headers = self.slsx_common_headers(request)
        headers.update(self.auth_header())

        response = requests.get(
            self.userinfo_endpoint + "/" + self.user_id,
            headers=headers,
            allow_redirects=False,
            verify=self.verify_ssl_internal,
            hooks={
                "response": [
                    response_hook_wrapper(sender=SLSxUserInfoResponse, request=request)
                ]
            },
        )
        self.userinfo_status_code = response.status_code
        response.raise_for_status()

        # Get data.user part of response
        data_user_response = response.json().get("data", {}).get("user", None)

        self.validate_asserts(
            request,
            [
                (
                    data_user_response is None
                    or data_user_response.get("id", None) is None,
                    MSG_SLS_RESP_MISSING_USERINFO_USERID,
                ),
                (
                    self.user_id != data_user_response.get("id", None),
                    MSG_SLS_RESP_NOT_MATCHED_USERINFO_USERID,
                ),
            ],
            MedicareCallbackExceptionType.USERINFO,
        )

        self.user_id = self.user_id.strip()

        # per BB2-850, need to handle the case where data_user_response has 'hicn', 'mbi' but the value is None.
        # canonicallize mbi, hicn and validate
        self.hicn = data_user_response.get("hicn")
        if self.hicn is not None and isinstance(self.hicn, str):
            self.hicn = self.hicn.strip()

        self.mbi = data_user_response.get("mbi")
        # Convert SLS's mbi to UPPER case.
        if self.mbi is not None and isinstance(self.mbi, str):
            self.mbi = self.mbi.strip().upper()

        # If MBI returned from SLSx is blank, set to None for hash logging
        if self.mbi == "":
            self.mbi = None

        fn = data_user_response.get("firstName", "")
        self.firstname = fn if fn else ""
        ln = data_user_response.get("lastName", "")
        self.lastname = ln if ln else ""
        em = data_user_response.get("email", "")
        self.email = em if em else ""

        # Validate:
        # 1. sls_subject (self.user_id) cannot be empty. TODO: Validate format too.
        # 2. sls_hicn cannot be empty or None
        # 3. sls_hicn must be str.
        self.validate_asserts(request, [
            (self.user_id == "", "User info sub cannot be empty"),
            (not self.hicn, "User info HICN cannot be empty or None."),
            (not isinstance(self.hicn, str), "User info HICN must be str."),
            (self.mbi is not None and not isinstance(self.mbi, str), "User info MBI must be str."),
        ], MedicareCallbackExceptionType.AUTHN_USERINFO)

        self.mbi_format_synthetic = is_mbi_format_synthetic(self.mbi)
        self.mbi_format_valid, self.mbi_format_msg = is_mbi_format_valid(self.mbi)

        self.hicn_hash = hash_hicn(self.hicn)
        self.mbi_hash = hash_mbi(self.mbi)

        return data_user_response

    def service_health_check(self, request):
        """
        Checks the SLSx service health check endpoint to see if it is online.
        This is used in the mymedicare_login() view at the start of the auth flow
        and will produce an exception if not successful. This is also used by
        the BB2 /health/external check.
        """
        headers = self.slsx_common_headers(request)

        response = requests.get(
            self.healthcheck_endpoint,
            headers=headers,
            allow_redirects=False,
            verify=self.verify_ssl_internal,
            timeout=1,
        )
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

        response = requests.get(
            self.signout_endpoint,
            headers=headers,
            allow_redirects=False,
            verify=self.verify_ssl_external,
        )
        self.signout_status_code = response.status_code
        response.raise_for_status()

        self.validate_asserts(
            request,
            [
                (
                    self.signout_status_code != status.HTTP_302_FOUND,
                    "SLSx signout response_code = {code}. Expecting HTTP_302_FOUND.".format(
                        code=self.signout_status_code
                    ),
                )
            ],
            MedicareCallbackExceptionType.SIGNOUT,
        )

    def validate_user_signout(self, request):
        """
        Performs a call to userinfo_endpoint to validate that the bene is
        signed out. When NOT signed out, an exception is thrown.
        This assumes the bene is signed out, if the userinfo endpoint returns
        a HTTP_403_FORBIDDEN respose and the auth_token is no longer valid.
        """
        headers = self.slsx_common_headers(request)
        headers.update(self.auth_header())

        response = requests.get(
            self.userinfo_endpoint + "/" + self.user_id,
            headers=headers,
            allow_redirects=False,
            verify=self.verify_ssl_internal,
            hooks={
                "response": [
                    response_hook_wrapper(sender=SLSxUserInfoResponse, request=request)
                ]
            },
        )
        self.validate_signout_status_code = response.status_code

        self.validate_asserts(
            request,
            [
                (
                    self.validate_signout_status_code != status.HTTP_403_FORBIDDEN,
                    "SLSx validate signout response_code = {code}. Expecting HTTP_403_FORBIDDEN.".format(
                        code=self.validate_signout_status_code
                    ),
                )
            ],
            MedicareCallbackExceptionType.VALIDATE_SIGNOUT,
        )

    def validate_asserts(self, request, asserts, err_enum):
        # asserts is a list of tuple : (boolean expression, err message)
        # iterate boolean expressions and log err message if the expression evalaute to true
        logger = logging.getLogger(logging.AUDIT_AUTHN_SLS_LOGGER, request)

        log_dict = {
            "type": "Authentication:start",
            "sls_status": "FAIL",
            "sls_status_mesg": None,
            "sls_signout_status_code": self.signout_status_code,
            "sls_token_status_code": self.token_status_code,
            "sls_userinfo_status_code": self.userinfo_status_code,
            "sls_validate_signout_status_code": self.validate_signout_status_code,
            "sub": None,
            "sls_mbi_format_valid": None,
            "sls_mbi_format_msg": None,
            "sls_mbi_format_synthetic": None,
            "sls_hicn_hash": None,
            "sls_mbi_hash": None,
        }

        for t in asserts:
            bexp = t[0]
            msg = t[1]
            if bexp:
                log_dict.update({"sls_status_mesg": msg})
                logger.info(log_dict)
                err = None
                if err_enum == MedicareCallbackExceptionType.TOKEN:
                    err = BBMyMedicareSLSxTokenException(settings.MEDICARE_ERROR_MSG)
                elif err_enum == MedicareCallbackExceptionType.USERINFO:
                    err = BBMyMedicareSLSxUserinfoException(settings.MEDICARE_ERROR_MSG)
                elif err_enum == MedicareCallbackExceptionType.SIGNOUT:
                    err = BBMyMedicareSLSxSignoutException(settings.MEDICARE_ERROR_MSG)
                elif err_enum == MedicareCallbackExceptionType.VALIDATE_SIGNOUT:
                    err = BBMyMedicareSLSxValidateSignoutException(
                        settings.MEDICARE_ERROR_MSG
                    )
                elif err_enum == MedicareCallbackExceptionType.VALIDATION_ERROR:
                    err = ValidationError(settings.MEDICARE_ERROR_MSG)
                elif err_enum == MedicareCallbackExceptionType.AUTHN_USERINFO:
                    err = BBMyMedicareCallbackAuthenticateSlsUserInfoValidateException(
                        settings.MEDICARE_ERROR_MSG
                    )
                else:
                    err = Exception(
                        "Unkown medicare callback exception type: {}".format(err_enum)
                    )
                raise err

    def log_event(self, request, extra):
        logger = logging.getLogger(logging.AUDIT_AUTHN_SLS_LOGGER, request)

        log_dict = {
            "type": "Authentication:start",
            "sub": self.user_id,
            "sls_status": "OK",
            "sls_status_mesg": None,
            "sls_signout_status_code": self.signout_status_code,
            "sls_token_status_code": self.token_status_code,
            "sls_userinfo_status_code": self.userinfo_status_code,
            "sls_validate_signout_status_code": self.validate_signout_status_code,
            "sls_mbi_format_valid": self.mbi_format_valid,
            "sls_mbi_format_msg": self.mbi_format_msg,
            "sls_mbi_format_synthetic": self.mbi_format_synthetic,
            "sls_hicn_hash": self.hicn_hash,
            "sls_mbi_hash": self.mbi_hash,
        }

        log_dict.update(extra)
        logger.info(log_dict)

    def log_authn_success(self, request, extra):
        logger = logging.getLogger(logging.AUDIT_AUTHN_SLS_LOGGER, request)
        log_dict = {
            "type": "Authentication:success",
            "sub": self.user_id,
            "user": None,
        }
        log_dict.update(extra)
        logger.info(log_dict)
