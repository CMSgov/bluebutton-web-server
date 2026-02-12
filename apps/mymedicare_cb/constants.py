from enum import Enum
from rest_framework import status
from rest_framework.exceptions import APIException

DEFAULT_USERNAME = '00112233-4455-6677-8899-aabbccddeeff'
DEFAULT_HICN_HASH = '50ad63a61f6bdf977f9796985d8d286a3d10476e5f7d71f16b70b1b4fbdad76b'
DEFAULT_FIRST_NAME = 'Hello'
DEFAULT_LAST_NAME = 'World'
DEFAULT_EMAIL = 'oscar@sesamestreet.gov'

ERR_MSG_HICN_EMPTY_OR_NONE = "User info HICN cannot be empty or None."
ERR_MSG_HICN_NOT_STR = "User info HICN must be str."
ERR_MSG_MBI_NOT_STR = "User info MBI must be str."

NETLOC_REGEX = r'dev\.accounts\.cms\.gov|test\.accounts\.cms\.gov|msls'
NETLOC_REGEX_SSO_SESSION = r'dev\.accounts\.cms\.gov|test\.medicare\.gov|msls'

MAX_HICN_HASH_LENGTH = 64
MAX_MBI_LENGTH = 11

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


class BBMyMedicareCallbackCrosswalkCreateException(APIException):
    # BB2-237 custom exception
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class BBMyMedicareCallbackCrosswalkUpdateException(APIException):
    # BB2-237 custom exception
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
