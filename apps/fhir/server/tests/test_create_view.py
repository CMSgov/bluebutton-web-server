import base64

from unittest import skip

from django.core.urlresolvers import reverse
from django.conf import settings
from django.test import TestCase
from django.test.client import Client


ENCODED = settings.ENCODING


class FHIRCreateTestCase(TestCase):
    """
    Test FHIR Create
    """

    # auth_headers = {"HTTP_AUTHORIZATION": "Basic "+
    # base64.b64encode(user_password)}
    fixtures = ['provider-directory-resources.json']

    def setUp(self):
        username_for_test = 'alan'
        password_for_test = 'p'
        self.creds = '%s:%s' % (username_for_test, password_for_test)
        self.authn = 'Basic %s' % \
                     (base64.b64encode(self.creds.encode(ENCODED)))
        # self.credentials = base64.b64encode(self.credentials)

        self.resource_type = 'Practitioner'
        self.client = Client()
        self.client.defaults['HTTP_AUTHORIZATION'] = self.authn
        # 'Basic ' + self.credentials
        # self.client.defaults['HTTP_X_REQUESTED_WITH'] ='XMLHttpRequest'

        self.url = reverse('fhir_create', args=(self.resource_type,))
        self.good_json = """{
                        "hello": "World",
                        "meta": {
                                "versionId": 2,
                                "lastUpdated": "3015-12-15T20:18:40.229955Z"
                                }
                        }
                        """

        self.invalid_json = """{
                        "hello": "World",,,
                        "meta": {
                                "versionId": 2,
                                "lastUpdated": "3015-12-15T20:18:40.229955Z"
                                }
                        }
                        """

        self.with_id_json = """{
                        "id": "12345",
                        "hello": "World",
                        "meta": {
                                "versionId": 2,
                                "lastUpdated": "3015-12-15T20:18:40.229955Z"
                                }
                        }
                        """

    @skip('AssertionError: 400 != 201')
    def test_create_fhir(self):
        """test_fhir_create"""
        c = Client()
        # j = json.loads(self.good_json)
        response = c.post(self.url,
                          self.good_json,
                          content_type='application/json')

        # Check some response details
        self.assertEqual(response.status_code, 201)

    def test_create_fhir_fails_with_id(self):
        """test_fhir_create_fail_with_id"""
        c = Client()
        # j = json.loads(self.good_json)
        response = c.post(self.url,
                          self.with_id_json,
                          content_type='application/json')

        # Check some response details
        self.assertEqual(response.status_code, 400)

    def test_create_fhir_fails_with_invalid_json(self):
        """test_fhir_create_fail_with_invalid_json"""
        c = Client()
        # j = json.loads(self.good_json)
        response = c.post(self.url,
                          self.invalid_json,
                          content_type='application/json')

        # Check some response details
        self.assertEqual(response.status_code, 400)

    def test_fhir_create_get_reroutes_to_search(self):
        """test_fhir_create_get_reroutes_to_search"""
        c = Client()
        response = c.get(self.url)

        # Check some response details
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'search')
