from django.test import TestCase
from django.test.client import Client
from django.urls import reverse
from django.conf import settings
from waffle.testutils import override_switch
from http import HTTPStatus
import json
from apps.constants import (
    AUTH_SIGNING_ALG_ES384,
    AUTH_SIGNING_ALG_RS384,
    CLIENT_CONFIDENTIAL_ASYMMETRIC,
    CLIENT_CREDENTIALS,
    PRIVATE_KEY_JWT,
)


class OpenIDConnectConfigurationTestCase(TestCase):
    """
    Test OpenIDConnectConfiguration URI
    """

    def setUp(self):
        self.client = Client()
        self.url = reverse('openid-configuration')

    def test_valid_response(self):
        """
        Valid User can login
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(
            response, reverse('oauth2_provider_v2:token-v2'))
        self.assertContains(response, reverse('openid_connect_userinfo_v2'))
        self.assertContains(response, "response_types_supported")
        self.assertContains(response, getattr(settings, 'HOSTNAME_URL'))
        response_content = response.content
        response_content = str(response_content, encoding='utf8')
        self.assertEqual(type(json.loads(response_content)), type({}))


class SmartConfigurationV3TestCase(TestCase):
    """
    Test SMART Configuration V3
    """

    def setUp(self):
        self.client = Client()
        self.url = reverse("smart_configuration_v3")

    @override_switch("v3_endpoints", active=True)
    def test_v3_config_fields(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.json()

        self.assertIn(CLIENT_CREDENTIALS, data.get("grant_types_supported", []))
        self.assertIn(CLIENT_CONFIDENTIAL_ASYMMETRIC, data.get("capabilities", []))
        self.assertEqual(
            data.get("token_endpoint_auth_methods_supported"), [PRIVATE_KEY_JWT]
        )
        self.assertEqual(
            data.get("token_endpoint_auth_signing_alg_values_supported"),
            [AUTH_SIGNING_ALG_RS384, AUTH_SIGNING_ALG_ES384],
        )
