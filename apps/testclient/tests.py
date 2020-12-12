import json
from django.core.management import call_command
from django.conf import settings
from django.test import TestCase
from django.test.client import Client
from django.urls import reverse
from httmock import all_requests, HTTMock
from unittest import skipIf
from waffle.testutils import override_switch
from .utils import test_setup


class BlueButtonClientApiUserInfoTest(TestCase):
    """
    Test the BlueButton API UserInfo Endpoint
    """

    def setUp(self):
        call_command('create_blue_button_scopes')
        call_command('create_test_user_and_application')
        self.testclient_setup = test_setup()
        self.token = "sample-token-string"
        self.client = Client(Authorization="Bearer %s" % (self.token))
        self.patient = settings.DEFAULT_SAMPLE_FHIR_ID
        self.username = settings.DEFAULT_SAMPLE_FHIR_ID
        self.another_patient = '20140000000001'

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
class BlueButtonClientApiFhirTest(TestCase):
    """
    Test the BlueButton API FHIR Endpoints requiring an access token.
    """

    def setUp(self):
        call_command('create_blue_button_scopes')
        call_command('create_test_user_and_application')
        self.testclient_setup = test_setup()
        self.token = "sample-token-string"
        self.client = Client(Authorization="Bearer %s" % (self.token))
        self.patient = settings.DEFAULT_SAMPLE_FHIR_ID
        self.another_patient = '20140000000001'

    def test_get_patient(self):
        """
        Test get patient
        """
        uri = "%s%s" % (
            self.testclient_setup['patient_uri'], self.patient)
        response = self.client.get(uri)
        self.assertEqual(response['Content-Type'], "application/json")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.patient)

    def test_get_patient_fhir(self):
        """
        Test get patient
        """
        uri = "%s%s" % (
            self.testclient_setup['patient_uri'], self.patient)
        response = self.client.get(uri, HTTP_ACCEPT='application/fhir+json')
        self.assertEqual(response['Content-Type'], "application/fhir+json")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.patient)

        # Test for search endpoint
        uri = self.testclient_setup['patient_uri']
        response = self.client.get(uri, HTTP_ACCEPT='application/fhir+json')
        self.assertEqual(response['Content-Type'], "application/fhir+json")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.patient)

    def test_get_patient_negative(self):
        """
        Ensure other patient ID is inaccessible.
        """
        uri = "%s%s" % (
            self.testclient_setup['patient_uri'], self.another_patient)
        response = self.client.get(uri)
        print(response.content)
        self.assertEqual(response.status_code, 404)

    def test_get_eob(self):
        """
        Test get eob
        """

        uri = "%s?patient=%s&count=12" % (
            self.testclient_setup['eob_uri'], self.patient)
        response = self.client.get(uri)
        response_data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        self.assertEqual(len(response_data['entry']), 12)
        self.assertEqual(
            response_data['entry'][0]['fullUrl'],
            "http://testserver/v1/fhir/ExplanationOfBenefit/carrier-20587716665")
        self.assertContains(response, "ExplanationOfBenefit")

    def test_bad_count(self):
        uri = "%s?patient=%s&count=10000000" % (
            self.testclient_setup['eob_uri'], self.patient)
        response = self.client.get(uri)
        self.assertEqual(response.status_code, 400)

    def test_bad_offset(self):
        uri = "%s?patient=%s&startIndex=asdf" % (
            self.testclient_setup['eob_uri'], self.patient)
        response = self.client.get(uri)
        self.assertEqual(response.status_code, 400)

    def test_offset_math(self):
        uri = "%s?patient=%s&count=12&startIndex=25" % (
            self.testclient_setup['eob_uri'], self.patient)
        response = self.client.get(uri)
        response_data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data['total'], 32)
        self.assertEqual(len(response_data['entry']), 7)
        previous_links = [data['url'] for data in response_data['link'] if data['relation'] == 'previous']
        next_links = [data['url'] for data in response_data['link'] if data['relation'] == 'next']
        first_links = [data['url'] for data in response_data['link'] if data['relation'] == 'first']
        self.assertEqual(len(previous_links), 1)
        self.assertEqual(len(next_links), 0)
        self.assertEqual(len(first_links), 1)
        self.assertIn('startIndex=13', previous_links[0])
        self.assertIn('startIndex=0', first_links[0])
        self.assertContains(response, "ExplanationOfBenefit")

    def test_get_eob_negative(self):
        """
        Ensure other patient info is not returned
        """
        uri = "%s?patient=%s" % (
            self.testclient_setup['eob_uri'], self.another_patient)
        response = self.client.get(uri)
        self.assertEqual(response.status_code, 403)

    def test_get_coverage(self):
        """
        Test get coverage
        """
        uri = "%s?beneficiary=%s" % (
            self.testclient_setup['coverage_uri'], self.patient)
        response = self.client.get(uri)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Coverage")
        self.assertContains(response, self.patient)

    def test_get_coverage_negative(self):
        """
        Test get coverage
        """
        uri = "%s?beneficiary=%s" % (
            self.testclient_setup['coverage_uri'], self.another_patient)
        response = self.client.get(uri)
        self.assertEqual(response.status_code, 403)


@skipIf(settings.OFFLINE, "Can't reach external sites.")
class BlueButtonClientApiFhirMetadataDiscoveryTest(TestCase):
    """
    Test the BlueButton Discovery Endpoints
    These are public URIs
    """

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


class BlueButtonClientApiOidcDiscoveryTest(TestCase):
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


class BlueButtonClientApiFhirMetaDataTest(TestCase):

    def setUp(self):
        self.client = Client()

    @override_switch('bfd_v2', active=True)
    def test_get_fhir_metadata(self):
        self._get_capability(False)
        self._get_capability(True)

    def _get_capability(self, v2):

        @all_requests
        def catchall(url, req):
            if url.path.startswith('/v1/fhir/metadata'):
                return {
                    'status_code': 200,
                    'content': {"resourceType": "CapabilityStatement",
                                "status": "active",
                                "date": "2020-12-11T21:54:21+00:00",
                                "publisher": "Centers for Medicare & Medicaid Services",
                                "kind": "instance",
                                "software": {
                                    "name": "Blue Button API: Direct",
                                    "version": "1.0.0-SNAPSHOT"
                                },
                                "implementation": {
                                    "description": "gov.cms.bfd:bfd-server-war",
                                    "url": "https://prod-sbx.bfd.cms.gov/v1/fhir"
                                },
                                "fhirVersion": "3.0.2",
                                "acceptUnknown": "extensions",
                                "format": ["application/json", "application/fhir+json"],
                                "rest": [{"mode": "server",
                                          "security": {}}]
                                },
                }
            elif url.path.startswith('/v2/fhir/metadata'):
                return {
                    'status_code': 200,
                    'content': {"resourceType": "CapabilityStatement",
                                "status": "active",
                                "date": "2020-12-11T21:53:27+00:00",
                                "publisher": "Centers for Medicare & Medicaid Services",
                                "kind": "instance",
                                "software": {
                                    "name": "Blue Button API: Direct",
                                    "version": "1.0.0-SNAPSHOT"
                                },
                                "implementation": {
                                    "description": "gov.cms.bfd:bfd-server-war",
                                    "url": "http://192.168.0.109:8000/v2/fhir"
                                },
                                "fhirVersion": "4.0.0",
                                "format": ["application/json", "application/fhir+json"],
                                "rest": [{"mode": "server",
                                          "security": {}}]
                                },
                }
            else:
                return {
                    'status_code': 404,
                    'content': {"not found"},
                }

        with HTTMock(catchall):
            response = self.client.get(reverse('fhir_conformance_metadata'),
                                       {'dummy': 'hello world', 'fhir_ver': 'r4'} if v2 else {'dummy': 'hello world'})

            self.assertEqual(response.status_code, 200)
            content = json.loads(response.content.decode("utf-8"))
            if v2:
                self.assertEqual(content['fhirVersion'], '4.0.0')
            else:
                self.assertEqual(content['fhirVersion'], '3.0.2')
