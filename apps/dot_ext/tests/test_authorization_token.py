import json
import os
from base64 import b64encode
from http import HTTPStatus
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlencode, urlparse

import jwt
from django.http import HttpRequest
from oauth2_provider.models import get_access_token_model
from oauthlib.oauth2.rfc6749.errors import InvalidRequestError
from waffle.testutils import override_switch

from apps.capabilities.models import ProtectedCapability
from apps.constants import (
    CLIENT_CREDENTIALS,
    CODE_CHALLENGE_METHOD_S256,
    TEST_APP_CLIENT_ID,
    TEST_APP_CLIENT_SECRET,
)
from apps.dot_ext.constants import (
    APPLICATION_DOES_NOT_HAVE_CLIENT_CREDENTIALS_ENABLED,
    APPLICATION_HAS_CLIENT_CREDENTIALS_ENABLED_NON_CLIENT_CREDENTIALS_AUTH_CALL_MADE,
    AUTH_CODE_TYPE,
    CC_SYSTEM_MEDICARE_NUMBER,
    CLEAR_HIGHER_ISS,
    CLIENT_ASSERTION_TYPE_VALUE,
    CLIENT_CREDENTIALS_TYPE,
    IDME_HIGHER_ISS,
    IDME_LOWER_ISS,
)
from apps.dot_ext.models import Application
from apps.dot_ext.utils import (
    get_application_from_data,
    get_application_from_meta,
    validate_app_is_active,
)
from apps.dot_ext.views import TokenView
from apps.test import BaseApiTest
from apps.versions import Versions

AccessToken = get_access_token_model()

# Note: HS256 is used in the JWTs here, despite it not being allowed by the actual endpoint, because we do not have a sample .pem


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
            redirect_uris=redirect_uri,
        )
        application.scope.add(capability_a, capability_b)

        # Identification from client_assertion (Private Key JWT)
        assertion = jwt.encode({'iss': application.client_id}, 'secret', algorithm='HS256')
        token_request_data = {
            'grant_type': CLIENT_CREDENTIALS,
            'redirect_uri': redirect_uri,
            'scope': 'patient/ExplanationOfBenefit.rs',
            'client_assertion_type': CLIENT_ASSERTION_TYPE_VALUE,
            'client_assertion': assertion,
        }
        body = urlencode(token_request_data)
        response = self.client.post(
            f'/v{Versions.V3}/o/token/', data=body, content_type='application/x-www-form-urlencoded'
        )

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert response.json()['message'] == APPLICATION_DOES_NOT_HAVE_CLIENT_CREDENTIALS_ENABLED.format(
            application.name
        )

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
            redirect_uris=redirect_uri,
        )
        application.scope.add(capability_a, capability_b)
        application.jwks_uri = 'https://test.com'
        application.allowed_auth_type = AUTH_CODE_TYPE  # need to set this to be able to generate auth code initially
        application.save()
        # user logs in
        request = HttpRequest()
        self.client.login(request=request, username='anna', password='123456')

        code_challenge = 'sZrievZsrYqxdnu2NVD603EiYBM18CuzZpwB-pOSZjo'

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
            'state': '0123456789abcdef',
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

        response = self.client.post(
            f'/v{Versions.V3}/o/token/', data=body, content_type='application/x-www-form-urlencoded'
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        assert response.json()['message'] == (
            APPLICATION_HAS_CLIENT_CREDENTIALS_ENABLED_NON_CLIENT_CREDENTIALS_AUTH_CALL_MADE.format(application.name)
        )

    def test_validate_client_credentials_request_raise_missing_params(self) -> None:
        view_instance = TokenView()
        mock_request = MagicMock()
        mock_request.POST = {'_encoding': 'utf-8', '_mutable': False}

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
            'scope': 'patient/ExplanationOfBenefit.rs',
            'client_assertion_type': CLIENT_ASSERTION_TYPE_VALUE,
            'client_assertion': 'test',
        }

        result = view_instance._validate_client_credentials_request(mock_request)
        assert result is None

    def test_validate_environment_for_id_token(self) -> None:
        """Confirm that, given a specific environment and an issuer URL, the
        _validate_idme_url_for_id_token_and_environment will correctly return True or False
        """
        view_instance = TokenView()
        os.environ['TARGET_ENV'] = 'prod'
        result = view_instance._validate_idme_url_for_id_token_and_environment(CLEAR_HIGHER_ISS)
        assert result

        result = view_instance._validate_idme_url_for_id_token_and_environment(IDME_LOWER_ISS)
        assert not result

        os.environ['TARGET_ENV'] = 'impl'
        result = view_instance._validate_idme_url_for_id_token_and_environment(IDME_HIGHER_ISS)
        assert not result

        os.environ['TARGET_ENV'] = 'test'
        result = view_instance._validate_idme_url_for_id_token_and_environment(IDME_HIGHER_ISS)
        assert not result

        os.environ['TARGET_ENV'] = 'local'
        result = view_instance._validate_idme_url_for_id_token_and_environment(IDME_HIGHER_ISS)
        assert not result

        result = view_instance._validate_idme_url_for_id_token_and_environment(IDME_LOWER_ISS)
        assert result

        os.environ['TARGET_ENV'] = 'prod'
        result = view_instance._validate_idme_url_for_id_token_and_environment(IDME_HIGHER_ISS)
        assert result


# we set empty GET/META/POST because get_application_from_data does not like it if a GET is missing.
class TestClientIdExtraction(BaseApiTest):
    def setUp(self):
        super().setUp()
        self.application = self._create_application(
            'Test App',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            client_type=Application.CLIENT_CONFIDENTIAL,
            redirect_uris='http://localhost',
        )

    def test_get_client_id_from_client_assertion(self):
        """Verify client_id extraction from JWT client_assertion (client_credentials path)."""
        assertion = jwt.encode({'iss': self.application.client_id}, 'secret', algorithm='HS256')
        mock_request = MagicMock(spec=HttpRequest)
        mock_request.POST = {'client_assertion': assertion}
        mock_request.GET = {}
        mock_request.META = {}

        app = get_application_from_data(mock_request)
        self.assertEqual(app, self.application)

    def test_get_client_id_from_post_data(self):
        """Verify client_id extraction from POST data (traditional path)."""
        mock_request = MagicMock(spec=HttpRequest)
        mock_request.POST = {'client_id': self.application.client_id}
        mock_request.GET = {}
        mock_request.META = {}

        app = get_application_from_data(mock_request)
        self.assertEqual(app, self.application)

    def test_get_client_id_from_get_data(self):
        """Verify client_id extraction from GET data."""
        mock_request = MagicMock(spec=HttpRequest)
        mock_request.POST = {}
        mock_request.GET = {'client_id': self.application.client_id}
        mock_request.META = {}

        app = get_application_from_data(mock_request)
        self.assertEqual(app, self.application)

    def test_get_client_id_from_basic_auth(self):
        """Verify client_id extraction from HTTP Basic Authorization header."""
        auth_str = f'{self.application.client_id}:dummy_secret'
        encoded_auth = b64encode(auth_str.encode('utf-8')).decode('utf-8')

        mock_request = MagicMock(spec=HttpRequest)
        mock_request.POST = {}
        mock_request.GET = {}
        mock_request.META = {'HTTP_AUTHORIZATION': f'Basic {encoded_auth}'}

        app = get_application_from_meta(mock_request)
        self.assertEqual(app, self.application)

    def test_validate_app_is_active_client_credentials_no_assertion(self):
        """Verify validate_app_is_active fails if grant_type=client_credentials but no assertion."""
        mock_request = MagicMock(spec=HttpRequest)
        mock_request.POST = {
            'grant_type': 'client_credentials',
            'client_id': self.application.client_id,
        }
        mock_request.GET = {}
        mock_request.META = {}

        with self.assertRaises(InvalidRequestError) as cm:
            validate_app_is_active(mock_request)
        self.assertIn(
            'Missing client_assertion',
            cm.exception.description,
        )

    def test_validate_app_is_active_client_credentials_with_assertion(self):
        """Verify validate_app_is_active succeeds for client_credentials with valid-looking assertion."""
        assertion = jwt.encode({'iss': self.application.client_id}, 'secret', algorithm='HS256')
        mock_request = MagicMock(spec=HttpRequest)
        mock_request.POST = {
            'grant_type': 'client_credentials',
            'client_assertion': assertion,
        }
        mock_request.GET = {}
        mock_request.META = {}

        app = validate_app_is_active(mock_request)
        self.assertEqual(app, self.application)


class TestTokenResponseFields(BaseApiTest):
    def setUp(self):
        super().setUp()
        # Create a patient user with a crosswalk
        self.patient_fhir_v3 = 'patient-123-v3'
        self.user = self._create_user('patient_user', 'password123', fhir_id_v3=self.patient_fhir_v3)

        # Since we care about exact capabilities, define it here explicitly
        capability_a, _ = ProtectedCapability.objects.get_or_create(
            title='patient/ExplanationOfBenefit.rs',
            slug='patient/ExplanationOfBenefit.rs',
            group=self._create_group('test'),
            default=True,
        )

        # Create an app allowed to use client_credentials
        self.application = self._create_application(
            'CC App',
            grant_type=Application.GRANT_CLIENT_CREDENTIALS,
            client_type=Application.CLIENT_CONFIDENTIAL,
            redirect_uris='http://localhost',
            allowed_auth_type=CLIENT_CREDENTIALS_TYPE,
            jwks_uri='https://example.com/jwks',
            client_id=TEST_APP_CLIENT_ID,
            client_secret=TEST_APP_CLIENT_SECRET,
        )
        self.application.scope.add(capability_a)

    @patch('apps.dot_ext.views.authorization.TokenView._validate_authorization_jwt')
    @patch('apps.dot_ext.views.authorization.TokenView._validate_ial_jwt')
    @patch('apps.dot_ext.views.authorization.TokenView._create_or_retrieve_user')
    @patch('apps.dot_ext.views.authorization.get_patient_match_response_json')
    @override_switch('v3_endpoints', active=True)
    def test_client_credentials_includes_patient_in_response(
        self, mock_get_patient, mock_create_user, mock_validate_ial, mock_validate_auth
    ):
        """Verify that the "patient" field is included in the token response for client_credentials"""

        # Mocking the matched user
        mock_create_user.return_value = self.user

        # Create fake JWT for first validation step
        internal_id_token = jwt.encode(
            {
                'iss': IDME_LOWER_ISS,
                'sub': '123',
                'aud': 'https://fake.bluebutton.cms.gov',
                'jti': 'jti-1',
                'exp': 9999999999,
                'iat': 1775317326,
            },
            'secret',
            algorithm='HS256',
        )
        mock_validate_auth.return_value = internal_id_token

        # min necessary fields (apart from address.)
        mock_validate_ial.return_value = {
            'iss': IDME_LOWER_ISS,
            'sub': '123',
            'jti': 'jti-2',
            'exp': 9999999999,
            'iat': 1775317326,
            'family_name': 'Smith',
            'given_name': 'John',
            'birthdate': '1970-01-01',
            'gender': 'Male',
        }

        # Mock patient match result
        # is_patient_match_found expects at least 2 entries in successful match
        mock_get_patient.return_value = {
            'entry': [
                {'resource': {'id': 'org-example', 'resourceType': 'Organization'}},
                {
                    'resource': {
                        'resourceType': 'Patient',
                        'id': self.patient_fhir_v3,
                        'identifier': [
                            {
                                'system': CC_SYSTEM_MEDICARE_NUMBER,
                                'value': self.test_mbi,
                            }
                        ],
                    }
                },
            ]
        }

        assertion = jwt.encode({'iss': self.application.client_id}, 'secret', algorithm='HS256')

        token_request_data = {
            'grant_type': CLIENT_CREDENTIALS,
            'client_assertion_type': CLIENT_ASSERTION_TYPE_VALUE,
            'client_assertion': assertion,
            'scope': 'patient/ExplanationOfBenefit.rs openid',
        }

        response = self.client.post(
            f'/v{Versions.V3}/o/token/',
            data=urlencode(token_request_data),
            content_type='application/x-www-form-urlencoded',
        )

        self.assertEqual(response.status_code, HTTPStatus.OK, response.content)
        data = response.json()

        self.assertIn('patient', data)
        self.assertEqual(data['patient'], self.patient_fhir_v3)
        self.assertIn('access_token', data)
        # see authorization.py -> we can revisit this, but UserInfo will not return anything in the client_credentials flow.
        self.assertNotIn('openid', data['scope'])
        # other scopes ought to be fine, however.
        self.assertIn('patient/ExplanationOfBenefit.rs', data['scope'])
