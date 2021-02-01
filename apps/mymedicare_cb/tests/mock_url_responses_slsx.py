import requests
from httmock import urlmatch

NETLOC_REGEX = r'dev\.accounts\.cms\.gov|test\.accounts\.cms\.gov'
NETLOC_REGEX_SSO_SESSION = r'dev\.accounts\.cms\.gov|test\.medicare\.gov'


class MockUrlSLSxResponses:
    '''
    This class contains mock url responses for the SLSx endpoints.

    This is used for tests in apps.logging/test_audit_loggers.py
    and apps/mymedicare/tests/test_callback_slsx.py
    '''
    # mock sls health check endpoint
    @urlmatch(netloc=NETLOC_REGEX, path='/health')
    def slsx_health_ok_mock(url, request):
        return {"status_code": 200}

    # mock sls health check endpoint with http error
    @urlmatch(netloc=NETLOC_REGEX, path='/health')
    def slsx_health_fail_mock(url, request):
        raise requests.exceptions.HTTPError

    @urlmatch(netloc=NETLOC_REGEX_SSO_SESSION, path='/sso/session')
    def slsx_token_mock(url, request):
        return {"status_code": 200,
                "content": {"auth_token": "tqXFB/j2OR9Fx7aDowGasMZGqoWmwcihNzMdaW2gpEmV",
                            "role": "consumer",
                            "user_id": "00112233-4455-6677-8899-aabbccddeeff",
                            "session_id": "47dc2799838c4a3cb0ad55c688f6de07"}}

    # mock sls token endpoint with http error
    @urlmatch(netloc=NETLOC_REGEX_SSO_SESSION, path='/sso/session')
    def slsx_token_http_error_mock(url, request):
        raise requests.exceptions.HTTPError

    # mock sls user info endpoint
    @urlmatch(netloc=NETLOC_REGEX, path='/v1/users/00112233-4455-6677-8899-aabbccddeeff')
    def slsx_user_info_mock(url, request):
        return {"status_code": 200,
                "content": {"status": "ok",
                            "code": 200,
                            "data": {"user": {"id": "00112233-4455-6677-8899-aabbccddeeff",
                                              "email": "bob@bobserver.bob",
                                              "firstName": None,
                                              "lastName": None,
                                              "hicn": "1234567890A",
                                              "customUserInfo": {"mbi": "1SA0A00AA00"},
                                              "mbi": "1SA0A00AA00"}}}}

    # mock sls user info endpoint with http error
    @urlmatch(netloc=NETLOC_REGEX, path='/v1/users/00112233-4455-6677-8899-aabbccddeeff')
    def slsx_user_info_http_error_mock(url, request):
        raise requests.exceptions.HTTPError

    # mock sls user info endpoint with out a sub/username
    @urlmatch(netloc=NETLOC_REGEX, path='/v1/users/00112233-4455-6677-8899-aabbccddeeff')
    def slsx_user_info_no_username_mock(url, request):
        return {"status_code": 200,
                "content": {"status": "ok",
                            "code": 200,
                            "data": {"user": {"email": "bob@bobserver.bob",
                                              "firstName": None,
                                              "lastName": None,
                                              "hicn": "1234567890A",
                                              "customUserInfo": {"mbi": "1SA0A00AA00"},
                                              "mbi": "1SA0A00AA00"}}}}

    # mock sls user info endpoint with missing hicn
    @urlmatch(netloc=NETLOC_REGEX, path='/v1/users/00112233-4455-6677-8899-aabbccddeeff')
    def slsx_user_info_empty_hicn_mock(url, request):
        return {"status_code": 200,
                "content": {"status": "ok",
                            "code": 200,
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
        return {"status_code": 200,
                "content": {"status": "ok",
                            "code": 200,
                            "data": {"user": {"id": "00112233-4455-6677-8899-aabbccddeeff",
                                              "email": "bob@bobserver.bob",
                                              "firstName": None,
                                              "lastName": None,
                                              "hicn": "1234567890A",
                                              "customUserInfo": {"mbi": "1SA0A00SS00"},
                                              "mbi": "1SA0A00SS00"}}}}
