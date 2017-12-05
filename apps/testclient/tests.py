from __future__ import absolute_import
from __future__ import unicode_literals
from django.core.management import call_command
from django.test.client import Client
from django.test import TestCase
from .utils import test_setup
from django.core.urlresolvers import reverse

__author__ = "Alan Viars"


class BlueButtonClientApiUSerInfoTest(TestCase):
    """
    Test the BlueButton API UserInfo Endpoint
    """

    fixtures = ['testfixture']

    def setUp(self):
        call_command('create_blue_button_scopes')
        call_command('create_test_user_and_application')
        self.testclient_setup = test_setup()
        self.token = "sample-token-string"
        self.client = Client(Authorization="Bearer %s" % (self.token))
        self.patient = "3979"
        self.username = "fred"

    def test_get_userinfo(self):
        """
        Test get userinfo
        """
        response = self.client.get(self.testclient_setup['userinfo_uri'])
        self.assertEqual(response.status_code, 200)
        jr = response.json()
        self.assertEqual(jr['patient'], self.patient)
        self.assertEqual(jr['sub'], self.username)


class BlueButtonClientApiOIDCDiscoveryTest(TestCase):
    """
    Test the BlueButton OIDC Discovery Endpoint
    Public URIs
    """

    def setUp(self):
        self.client = Client()

    def test_get_oidc_discovery(self):
        """
        Test get oidc discovery
        """
        response = self.client.get(reverse('openid-configuration'))
        self.assertEqual(response.status_code, 200)
        # jr = response.json()
        self.assertContains(response, "userinfo_endpoint")
