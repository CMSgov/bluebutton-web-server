import json
from datetime import timedelta
from oauthlib.oauth2.rfc6749.errors import InvalidRequestError
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError
from oauth2_provider.models import get_access_token_model, get_refresh_token_model
from django.utils import timezone
from unittest.mock import MagicMock
from unittest import skipIf
from urllib.parse import urlencode
from waffle.testutils import override_switch
from apps.constants import (
    CLIENT_CREDENTIALS,
    TEST_APP_CLIENT_ID,
    TEST_APP_CLIENT_SECRET,
    USER_TYPE_ALIGNED_NETWORKS_BENEFICIARY,
)
from apps.accounts.models import UserProfile
from apps.dot_ext.constants import (
    APPLICATION_DOES_NOT_HAVE_CLIENT_CREDENTIALS_ENABLED,
    APPLICATION_HAS_CLIENT_CREDENTIALS_ENABLED_NON_CLIENT_CREDENTIALS_AUTH_CALL_MADE,
    CLIENT_ASSERTION_TYPE_VALUE,
    CLIENT_CREDENTIALS_ACCESS_TOKEN_LIFETIME,
    CLIENT_CREDENTIALS_REFRESH_WINDOW,
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
    @skipIf(
        True,
        'skipping for now as 4699 throws an error in the authorize of post if the grant_type is not allowed for the app'
    )
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
        application.allowed_auth_type = CLIENT_CREDENTIALS.upper()
        application.save()
        token_request_data = {
            'grant_type': 'authorization_code',
            'code': 'dummy-auth-code',
            'redirect_uri': redirect_uri,
            'client_id': application.client_id,
        }
        body = urlencode(token_request_data)
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

    def test_apply_client_credentials_access_token_lifetime(self) -> None:
        view_instance = TokenView()

        application = self._create_application(
            'cc app lifetime',
            grant_type=Application.GRANT_CLIENT_CREDENTIALS,
            client_type=Application.CLIENT_CONFIDENTIAL,
            redirect_uris='http://localhost',
        )
        user = self._create_user('cc_lifetime_user', 'pw')

        token = AccessToken.objects.create(
            user=user,
            token='cc-lifetime-token',
            application=application,
            expires=timezone.now() + timedelta(days=1),
        )

        body = {'expires_in': 36000}
        view_instance._apply_client_credentials_access_token_lifetime(token, body)
        token.refresh_from_db()

        self.assertEqual(body['expires_in'], int(CLIENT_CREDENTIALS_ACCESS_TOKEN_LIFETIME.total_seconds()))
        expected_expires = timezone.now() + CLIENT_CREDENTIALS_ACCESS_TOKEN_LIFETIME
        self.assertLessEqual(abs((token.expires - expected_expires).total_seconds()), 5)

    def test_validate_client_credentials_refresh_window_expired(self) -> None:
        view_instance = TokenView()

        application = self._create_application(
            'cc app refresh',
            grant_type=Application.GRANT_CLIENT_CREDENTIALS,
            client_type=Application.CLIENT_CONFIDENTIAL,
            redirect_uris='http://localhost',
        )
        user = self._create_user('cc_refresh_user', 'pw')
        UserProfile.objects.update_or_create(
            user=user,
            defaults={'user_type': USER_TYPE_ALIGNED_NETWORKS_BENEFICIARY},
        )
        user.crosswalk.user_id_type = 'M'
        user.crosswalk.save(update_fields=['user_id_type'])

        access_token = AccessToken.objects.create(
            user=user,
            token='cc-refresh-token',
            application=application,
            expires=timezone.now() + timedelta(hours=1),
        )
        refresh_token = RefreshToken.objects.create(
            user=user,
            token='cc-refresh-token-value',
            application=application,
            access_token=access_token,
        )

        access_token.created = timezone.now() - CLIENT_CREDENTIALS_REFRESH_WINDOW - timedelta(seconds=1)
        access_token.expires = access_token.created + CLIENT_CREDENTIALS_ACCESS_TOKEN_LIFETIME
        access_token.save(update_fields=['created', 'expires'])

        with self.assertRaises(InvalidGrantError):
            view_instance._validate_client_credentials_refresh_window(refresh_token)

    def test_validate_client_credentials_refresh_window_ignores_non_anb_user(self) -> None:
        view_instance = TokenView()

        application = self._create_application(
            'cc app refresh non anb',
            grant_type=Application.GRANT_CLIENT_CREDENTIALS,
            client_type=Application.CLIENT_CONFIDENTIAL,
            redirect_uris='http://localhost',
        )
        user = self._create_user('cc_non_anb_refresh_user', 'pw')

        access_token = AccessToken.objects.create(
            user=user,
            token='cc-refresh-token-non-anb',
            application=application,
            expires=timezone.now() + timedelta(hours=1),
        )
        refresh_token = RefreshToken.objects.create(
            user=user,
            token='cc-refresh-token-value-non-anb',
            application=application,
            access_token=access_token,
        )

        access_token.created = timezone.now() - CLIENT_CREDENTIALS_REFRESH_WINDOW - timedelta(seconds=1)
        access_token.expires = access_token.created + CLIENT_CREDENTIALS_ACCESS_TOKEN_LIFETIME
        access_token.save(update_fields=['created', 'expires'])

        # Non-ANB beneficiaries should not use client_credentials refresh-chain expiration checks.
        view_instance._validate_client_credentials_refresh_window(refresh_token)

    def test_is_client_credentials_access_token_uses_token_lifetime_for_refresh(self) -> None:
        view_instance = TokenView()

        application = self._create_application(
            'cc token-tied refresh app',
            grant_type=Application.GRANT_AUTHORIZATION_CODE,
            client_type=Application.CLIENT_CONFIDENTIAL,
            redirect_uris='http://localhost',
        )
        user = self._create_user('cc_token_tied_user', 'pw')
        UserProfile.objects.update_or_create(
            user=user,
            defaults={'user_type': USER_TYPE_ALIGNED_NETWORKS_BENEFICIARY},
        )
        user.crosswalk.user_id_type = 'M'
        user.crosswalk.save(update_fields=['user_id_type'])

        access_token = AccessToken.objects.create(
            user=user,
            token='cc-token-tied-refresh-token',
            application=application,
            expires=timezone.now() + CLIENT_CREDENTIALS_ACCESS_TOKEN_LIFETIME,
        )

        self.assertTrue(
            view_instance._is_client_credentials_access_token(access_token, 'refresh_token')
        )
