from django.test import TestCase
from django.test.client import Client
from django.urls import reverse
from django.utils import six
from django.conf import settings
import json


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
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, reverse('oauth2_provider:token'))
        self.assertContains(response, reverse('openid_connect_userinfo'))
        self.assertContains(response, "response_types_supported")
        self.assertContains(response, getattr(settings, 'HOSTNAME_URL'))
        response_content = response.content
        if six.PY3:
            response_content = str(response_content, encoding='utf8')
        self.assertEqual(type(json.loads(response_content)), type({}))
