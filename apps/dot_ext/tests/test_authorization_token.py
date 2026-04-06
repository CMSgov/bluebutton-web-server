import json
from oauthlib.oauth2.rfc6749.errors import InvalidRequestError
from oauth2_provider.models import get_access_token_model, get_refresh_token_model
from django.http import HttpRequest
from unittest.mock import MagicMock
from unittest import skipIf
from urllib.parse import parse_qs, urlencode, urlparse
from waffle.testutils import override_switch
from apps.constants import CLIENT_CREDENTIALS, CODE_CHALLENGE_METHOD_S256, TEST_APP_CLIENT_ID, TEST_APP_CLIENT_SECRET
from apps.dot_ext.constants import (
    APPLICATION_DOES_NOT_HAVE_CLIENT_CREDENTIALS_ENABLED,
    APPLICATION_HAS_CLIENT_CREDENTIALS_ENABLED_NON_CLIENT_CREDENTIALS_AUTH_CALL_MADE,
    CLIENT_ASSERTION_TYPE_VALUE,
    CLIENT_CREDENTIALS_TYPE,
    AUTH_CODE_TYPE,
)
from apps.dot_ext.models import Application
from apps.dot_ext.views import TokenView
from apps.test import BaseApiTest
from apps.versions import Versions
from http import HTTPStatus

AccessToken = get_access_token_model()
RefreshToken = get_refresh_token_model()


class TestAuthorizeTokenEndpoint(BaseApiTest):

    def test_check_if_client_credentials_call_is_allowed(self) -> None:
        view_instance = TokenView()
        mock_app = Application(name='TestApp', allowed_auth_type='AUTH_CODE', jwks_uri='https://valid.jwks.json')

        result = view_instance._check_if_client_credentials_call_is_allowed(mock_app, Versions.V1)
        assert not result

        result = view_instance._check_if_client_credentials_call_is_allowed(mock_app, Versions.V2)
        assert not result

        result = view_instance._check_if_client_credentials_call_is_allowed(mock_app, Versions.V3)
        assert not result

        mock_app.allowed_auth_type = 'AUTH_CODE_AND_CLIENT_CREDS'
        result = view_instance._check_if_client_credentials_call_is_allowed(mock_app, Versions.V3)
        assert result

        mock_app.allowed_auth_type = 'CLIENT_CREDENTIALS'
        result = view_instance._check_if_client_credentials_call_is_allowed(mock_app, Versions.V3)
        assert result

    @override_switch('v3_endpoints', active=True)
    @skipIf(True, 'skip')
    def test_client_credentials(self):
        """Ensure a bad request is thrown when a v3 token calls is made, with grant_type = client_credentials
        and the application for the request does not have allowed_auth_type in
        ['AUTH_CODE_AND_CLIENT_CREDS', 'CLIENT_CREDENTIALS']
        """
        redirect_uri = 'http://localhost'
        # create a user
        self._create_user('anna', '123456')

        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            client_type=Application.CLIENT_CONFIDENTIAL,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b)

        # I believe we only want to test the token endpoint, without hitting authorize first
        token_request_data = {
            'grant_type': CLIENT_CREDENTIALS,
            'redirect_uri': redirect_uri,
            'client_id': application.client_id,
            'client_secret': application.client_secret_plain,
            'scope': 'patient/ExplanationOfBenefit.rs',
            'client_assertion_type': CLIENT_ASSERTION_TYPE_VALUE,
            'client_assertion': 'test',
        }
        body = urlencode(token_request_data)
        response = self.client.post(f'/v{Versions.V3}/o/token/', data=body, content_type='application/x-www-form-urlencoded')

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert response.json()['message'] == APPLICATION_DOES_NOT_HAVE_CLIENT_CREDENTIALS_ENABLED.format(application.name)

    @override_switch('v3_endpoints', active=True)
    def test_authorization_code_grant_type_when_app_is_only_allowed_client_credentials(self):
        """Purpose of this test is to show that if a call is made to the token endpoint, and the app has
        allowed_auth_type of CLIENT_CREDENTIALS, and the grant_type is not client_credentials, that a 403 error
        with a specific message will be returned
        """
        redirect_uri = 'com.custom.bluebutton://example.it'
        # create a user
        self._create_user('anna', '123456')
        capability_a = self._create_capability('Capability A', [])
        capability_b = self._create_capability('Capability B', [])
        # create an application and add capabilities
        application = self._create_application(
            'an app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            client_type=Application.CLIENT_PUBLIC,
            redirect_uris=redirect_uri)
        application.scope.add(capability_a, capability_b)
        application.jwks_uri = 'https://test.com'
        application.allowed_auth_type = AUTH_CODE_TYPE   # need to set this to be able to generate auth code initially
        application.save()
        # user logs in
        request = HttpRequest()
        self.client.login(request=request, username='anna', password='123456')

        code_challenge = "sZrievZsrYqxdnu2NVD603EiYBM18CuzZpwB-pOSZjo"

        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'code_challenge': code_challenge,
            'code_challenge_method': CODE_CHALLENGE_METHOD_S256,
        }
        response = self.client.get('/v3/o/authorize', data=payload)
        # post the authorization form with only one scope selected
        payload = {
            'client_id': application.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ['capability-a'],
            'expires_in': 86400,
            'allow': True,
            "state": "0123456789abcdef",
            'code_challenge': code_challenge,
            'code_challenge_method': CODE_CHALLENGE_METHOD_S256,
        }
        response = self.client.post(response['Location'], data=payload)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        query_dict = parse_qs(urlparse(response['Location']).query)
        authorization_code = query_dict.pop('code')
        token_request_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': redirect_uri,
            'client_id': application.client_id,
        }
        body = urlencode(token_request_data)

        application.allowed_auth_type = CLIENT_CREDENTIALS_TYPE  # update to disable auth code based token
        application.save()

        response = self.client.post(f'/v{Versions.V3}/o/token/', data=body, content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        assert response.json()['message'] == (
            APPLICATION_HAS_CLIENT_CREDENTIALS_ENABLED_NON_CLIENT_CREDENTIALS_AUTH_CALL_MADE.format(application.name)
        )

    def test_validate_client_credentials_request_raise_missing_params(self) -> None:
        view_instance = TokenView()
        mock_request = MagicMock()
        mock_request.POST = {
            '_encoding': 'utf-8',
            '_mutable': False
        }

        # Pass the mock request to your function
        result = view_instance._validate_client_credentials_request(mock_request)
        result_dict = json.loads(result.content)
        assert result_dict['status_code'] == HTTPStatus.BAD_REQUEST
        assert result_dict['message'] == (
            'Missing Required Parameter(s): grant_type, scope, client_assertion_type, client_assertion'
        )

    def test_validate_client_credentials_request_raise_invalid_request(self) -> None:
        view_instance = TokenView()
        mock_request = MagicMock()
        mock_request.POST = {
            'grant_type': CLIENT_CREDENTIALS,
            'redirect_uri': 'test.com',
            'client_id': TEST_APP_CLIENT_ID,
            'client_secret': TEST_APP_CLIENT_SECRET,
            'scope': 'patient/ExplanationOfBenefit.rs',
            'client_assertion_type': 'incorrect-assertion',
            'client_assertion': 'test',
        }

        with self.assertRaises(InvalidRequestError):
            view_instance._validate_client_credentials_request(mock_request)

    def test_validate_client_credentials_request(self) -> None:
        view_instance = TokenView()
        mock_request = MagicMock()
        mock_request.POST = {
            'grant_type': CLIENT_CREDENTIALS,
            'redirect_uri': 'test.com',
            'client_id': TEST_APP_CLIENT_ID,
            'client_secret': TEST_APP_CLIENT_SECRET,
            'scope': 'patient/ExplanationOfBenefit.rs',
            'client_assertion_type': CLIENT_ASSERTION_TYPE_VALUE,
            'client_assertion': 'test',
        }

        result = view_instance._validate_client_credentials_request(mock_request)
        assert result is None
