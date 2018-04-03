from django.core.urlresolvers import reverse
from django.test import TestCase
from urllib.parse import urlparse, parse_qs

__author__ = "Alan Viars"


class MyMedicareBlueButtonClientApiUserInfoTest(TestCase):
    """
    Tests for the MyMedicare login and SLS Callback
    """

    def setUp(self):
        self.callback_url = reverse('mymedicare-sls-callback')
        self.login_url = reverse('mymedicare-login')

    def test_login_url_success(self):
        """
        Test well-formed login_url has expected content
        """
        fake_login_url = 'https://example.com/login?scope=openid'

        with self.settings(ALLOW_CHOOSE_LOGIN=False, MEDICARE_LOGIN_URI=fake_login_url, MEDICARE_REDIRECT_URI='/123'):
            response = self.client.get(self.login_url + '?next=/')
            self.assertEqual(response.status_code, 302)
            query = parse_qs(urlparse(response['Location']).query)
            path = response['Location'].split('?')[0]
            self.assertEqual(path, 'https://example.com/login')
            self.assertEqual(query['redirect_uri'][0], '/123')

    def test_callback_url(self):
        """
        Test callback_url returns HTTP 400 when
        necessary GET parameter state is missing.
        """
        response = self.client.get(self.callback_url)
        self.assertEqual(response.status_code, 400)
