from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.conf import settings

class OpenIDConnectConfigurationTestCase(TestCase):
    """
    Test NOpenIDConnectConfiguration URL
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
        self.assertContains(response, reverse('oauth2_provider:token'))
        self.assertContains(response, reverse('openid_connect_userinfo'))
                            