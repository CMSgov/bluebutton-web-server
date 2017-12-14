from __future__ import absolute_import
from __future__ import unicode_literals
from django.core.management import call_command
from django.test.client import Client
from django.test import TestCase
from .utils import test_setup
from django.core.urlresolvers import reverse
from unittest import skipIf
from django.conf import settings

from django.conf.global_settings import settings

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
        # self.patient = "3979"
        self.patient = settings.DEFAULT_SAMPLE_FHIR_ID
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


@skipIf(settings.OFFLINE, "Can't reach external sites.")
class BlueButtonClientApiFHIRTest(TestCase):
    """
    Test the BlueButton API FHIR Endpoints requiring an access token.
    """

    fixtures = ['testfixture']

    def setUp(self):

        call_command('create_blue_button_scopes')
        call_command('create_test_user_and_application')
        self.testclient_setup = test_setup()
        self.token = "sample-token-string"
        self.client = Client(Authorization="Bearer %s" % (self.token))
        self.patient = settings.DEFAULT_SAMPLE_FHIR_ID

    def test_get_patient(self):
        """
        Test get patient
        """
        uri = "%s%s?format=json" % (
            self.testclient_setup['patient_uri'], self.patient)
        response = self.client.get(uri)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.patient)

    def test_get_eob(self):
        """
        Test get eob
        """
        uri = "%s?patient=%sformat=json" % (
            self.testclient_setup['eob_uri'], self.patient)
        response = self.client.get(uri)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ExplanationOfBenefit")

    def test_get_coverage(self):
        """
        Test get coverage
        """
        uri = "%s/?format=json" % (self.testclient_setup['coverage_uri'])
        response = self.client.get(uri)
        self.assertEqual(response.status_code, 200)


@skipIf(settings.OFFLINE, "Can't reach external sites.")
class BlueButtonClientApiFHIRMEetadataDiscoveryTest(TestCase):
    """
    Test the BlueButton Discovery Endpoints
    These are public URIs
    """

    fixtures = ['testfixture']

    def setUp(self):
        self.client = Client()

    def test_get_fhir_metadata(self):
        """
        Test get fhir metadata discovery
        """
        response = self.client.get(
            reverse('fhir_conformance_metadata') + "?format=json")
        self.assertEqual(response.status_code, 200)
        jr = response.json()
        self.assertEqual(jr['resourceType'], "CapabilityStatement")
        self.assertContains(
            response, "http://fhir-registry.smarthealthit.org/StructureDefinition/oauth-uris")


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
        self.assertContains(response, "userinfo_endpoint")
