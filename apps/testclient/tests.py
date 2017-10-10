from __future__ import absolute_import
from __future__ import unicode_literals
from django.core.management import call_command
from django.test.client import Client
from django.test import TestCase
from .utils import test_setup

__author__ = "Alan Viars"


class BlueButtonClientApiTest(TestCase):
    """
    Test the BlueButton API Client
    """

    def setUp(self):

        call_command('create_blue_button_scopes')
        call_command('create_test_user_and_application')
        self.username = "fred"
        self.password = "foobarfoobarfoobar"
        self.client.login(username=self.username, password=self.username)
        self.application = test_setup()
        self.token = "sample-token-string"
        self.client = Client(Authorization="Bearer %s" % (self.token))
        self.patient = "3979"

    def test_get_userinfo(self):
        """
        Test get userinfo
        """
        # print("client_id: ", self.application['client_id'])
        # print("access_token: ", self.token)
        # print("userinfo_uri: ", self.application['userinfo_uri'])
        response = self.client.get(self.application['userinfo_uri'])
        self.assertEqual(response.status_code, 200)
        jr = response.json()
        self.assertEqual(jr['patient'], self.patient)
        self.assertEqual(jr['sub'], self.username)
