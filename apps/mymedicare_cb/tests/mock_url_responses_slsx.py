import inspect
import requests
from httmock import urlmatch
from rest_framework import status


NETLOC_REGEX = r'dev\.accounts\.cms\.gov|test\.accounts\.cms\.gov|msls'
NETLOC_REGEX_SSO_SESSION = r'dev\.accounts\.cms\.gov|test\.medicare\.gov|msls'


def is_called_by_validate_user_signout():
    """
    Returns TRUE if called upstream by validate_user_signout method.

    This is used to change the mock return of the SLSx userinfo endpoint when
    called by the OAuth2ConfigSLSx.validate_user_signout() method.
    """
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    for i in calframe:
        if str(i.function) == "validate_user_signout":
            return True
    return False


class MockUrlSLSxResponses:
    '''
    This class contains mock url responses for the SLSx endpoints.

    This is used for tests in apps.logging/test_audit_loggers.py
    and apps/mymedicare/tests/test_callback_slsx.py
    '''
    # mock sls health check endpoint
    @urlmatch(netloc=NETLOC_REGEX, path='/health')
    def slsx_health_ok_mock(url, request):
        return {"status_code": status.HTTP_200_OK}

    # mock sls health check endpoint with http error
    @urlmatch(netloc=NETLOC_REGEX, path='/health')
    def slsx_health_fail_mock(url, request):
        raise requests.exceptions.HTTPError

    # mock sls signout endpoint OK
    @urlmatch(netloc=NETLOC_REGEX_SSO_SESSION, path='/sso/signout')
    def slsx_signout_ok_mock(url, request):
        return {'status_code': status.HTTP_302_FOUND,
                'Location': 'https://test.medicare.gov/mbp/signout.aspx'}

    # mock sls signout endpoint not-found
    @urlmatch(netloc=NETLOC_REGEX_SSO_SESSION, path='/sso/signout')
    def slsx_signout_fail_mock(url, request):
        return {"status_code": status.HTTP_404_NOT_FOUND}

    # mock sls signout endpoint OK
    @urlmatch(netloc=NETLOC_REGEX_SSO_SESSION, path='/sso/signout')
    def slsx_signout_fail2_mock(url, request):
        return {"status_code": status.HTTP_200_OK}

    # mock sls token endpoint OK
    @urlmatch(netloc=NETLOC_REGEX_SSO_SESSION, path='/sso/session')
    def slsx_token_mock(url, request):
        return {"status_code": status.HTTP_200_OK,
                "content": {"auth_token": "tqXFB/j2OR9Fx7aDowGasMZGqoWmwcihNzMdaW2gpEmV",
                            "role": "consumer",
                            "user_id": "00112233-4455-6677-8899-aabbccddeeff",
                            "session_id": "47dc2799838c4a3cb0ad55c688f6de07"}}

    @urlmatch(netloc=NETLOC_REGEX_SSO_SESSION, path='/sso/session')
    def slsx_token_non_json_response_mock(url, request):
        # pick a non 200 just fake an error response
        return {"status_code": 403,
                "content": "<div>Hey something went wrong with token service!</div>"}

    # mock sls token endpoint with http error
    @urlmatch(netloc=NETLOC_REGEX_SSO_SESSION, path='/sso/session')
    def slsx_token_http_error_mock(url, request):
        raise requests.exceptions.HTTPError

    # below urlmatch still use /v1/users..., since SLSX endpoints use v1 in path
    # mock sls user info endpoint
    @urlmatch(netloc=NETLOC_REGEX, path='/v1/users/00112233-4455-6677-8899-aabbccddeeff')
    def slsx_user_info_mock(url, request):
        if is_called_by_validate_user_signout():
            return {"status_code": status.HTTP_403_FORBIDDEN}
        else:
            return {"status_code": status.HTTP_200_OK,
                    "content": {"status": "ok",
                                "code": status.HTTP_200_OK,
                                "data": {"user": {"id": "00112233-4455-6677-8899-aabbccddeeff",
                                                  "email": "bob@bobserver.bob",
                                                  "firstName": None,
                                                  "lastName": None,
                                                  "hicn": "1234567890A",
                                                  "customUserInfo": {"mbi": "1SA0A00AA00"},
                                                  "mbi": "1SA0A00AA00"}}}}

    @urlmatch(netloc=NETLOC_REGEX, path='/v1/users/00112233-4455-6677-8899-aabbccddeeff')
    def slsx_user_info_non_json_response_mock(url, request):
        # pick a non 200 for a fake error
        return {"status_code": 403,
                "content": "<div>Hey something went wrong with user info service!</div>"}

    # mock sls user info endpoint with http error
    @urlmatch(netloc=NETLOC_REGEX, path='/v1/users/00112233-4455-6677-8899-aabbccddeeff')
    def slsx_user_info_http_error_mock(url, request):
        if is_called_by_validate_user_signout():
            return {"status_code": status.HTTP_403_FORBIDDEN}
        else:
            raise requests.exceptions.HTTPError("HTTPError status message")

    # mock sls user info endpoint with out a sub/username
    @urlmatch(netloc=NETLOC_REGEX, path='/v1/users/00112233-4455-6677-8899-aabbccddeeff')
    def slsx_user_info_no_username_mock(url, request):
        if is_called_by_validate_user_signout():
            return {"status_code": status.HTTP_403_FORBIDDEN}
        else:
            return {"status_code": status.HTTP_200_OK,
                    "content": {"status": "ok",
                                "code": status.HTTP_200_OK,
                                "data": {"user": {"email": "bob@bobserver.bob",
                                                  "firstName": None,
                                                  "lastName": None,
                                                  "hicn": "1234567890A",
                                                  "customUserInfo": {"mbi": "1SA0A00AA00"},
                                                  "mbi": "1SA0A00AA00"}}}}

    # mock sls user info endpoint with missing hicn
    @urlmatch(netloc=NETLOC_REGEX, path='/v1/users/00112233-4455-6677-8899-aabbccddeeff')
    def slsx_user_info_empty_hicn_mock(url, request):
        if is_called_by_validate_user_signout():
            return {"status_code": status.HTTP_403_FORBIDDEN}
        else:
            return {"status_code": status.HTTP_200_OK,
                    "content": {"status": "ok",
                                "code": status.HTTP_200_OK,
                                "data": {"user": {"id": "00112233-4455-6677-8899-aabbccddeeff",
                                                  "email": "bob@bobserver.bob",
                                                  "firstName": None,
                                                  "lastName": None,
                                                  "hicn": "",
                                                  "customUserInfo": {"mbi": "1SA0A00AA00"},
                                                  "mbi": "1SA0A00AA00"}}}}

    # mock sls user info endpoint with invalid MBI
    @urlmatch(netloc=NETLOC_REGEX, path='/v1/users/00112233-4455-6677-8899-aabbccddeeff')
    def slsx_user_info_invalid_mbi_mock(url, request):
        if is_called_by_validate_user_signout():
            return {"status_code": status.HTTP_403_FORBIDDEN}
        else:
            return {"status_code": status.HTTP_200_OK,
                    "content": {"status": "ok",
                                "code": status.HTTP_200_OK,
                                "data": {"user": {"id": "00112233-4455-6677-8899-aabbccddeeff",
                                                  "email": "bob@bobserver.bob",
                                                  "firstName": None,
                                                  "lastName": None,
                                                  "hicn": "1234567890A",
                                                  "customUserInfo": {"mbi": "1SA0A00SS00"},
                                                  "mbi": "1SA0A00SS00"}}}}
