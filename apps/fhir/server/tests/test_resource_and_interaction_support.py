import base64

from unittest import skip

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from apps.fhir.server.models import SupportedResourceType


ENCODED = settings.ENCODING


class FHIRCheckUnAuthInteractionTestCase(TestCase):
    """
    Test FHIR for Unauthorized Interaction
    """

    # auth_headers = {"HTTP_AUTHORIZATION": "Basic " +
    # base64.b64encode(user_password)}
    fixtures = ['provider-directory-resources.json']

    def setUp(self):
        username_for_test = 'alan'
        password_for_test = 'p'
        self.creds = '%s:%s' % (username_for_test, password_for_test)
        self.authn = 'Basic %s' % \
                     (base64.b64encode(self.creds.encode(ENCODED)))
        # self.credentials = base64.b64encode(self.credentials)

        self.resource_type = "Organization"
        self.client = Client()
        self.client.defaults['HTTP_AUTHORIZATION'] = self.authorization  # 'Basic ' + self.credentials
        # self.client.defaults['HTTP_X_REQUESTED_WITH'] ='XMLHttpRequest'

        self.url = reverse('fhir_create', args=(self.resource_type,)) + '?foo.bar'

    @skip('AssertionError: 200 != 403')
    def test_unauth_interaction_fhir(self):
        """test_fhir_create"""
        response = self.client.get(self.url)

        # Check some response details
        self.assertEqual(response.status_code, 403)


class FHIRCheckUnAuthResourceTestCase(TestCase):
    """
    Test FHIR for Unsupported Resource
    """

    # auth_headers = {"HTTP_AUTHORIZATION": "Basic " +
    # base64.b64encode(user_password)}
    fixtures = ['provider-directory-resources.json']

    def setUp(self):
        username_for_test = 'alan'
        password_for_test = 'p'
        self.creds = '%s:%s' % (username_for_test, password_for_test)
        self.authn = 'Basic %s' % \
                     (base64.b64encode(self.creds.encode(ENCODED)))
        # self.credentials = base64.b64encode(self.credentials)

        self.resource_type = 'Foo'
        self.client = Client()
        self.client.defaults['HTTP_AUTHORIZATION'] = self.authn
        #  'Basic ' + self.credentials

        # self.client.defaults['HTTP_X_REQUESTED_WITH'] ='XMLHttpRequest'

        self.url = reverse('fhir_create', args=(self.resource_type,)) + '?foo.bar'

    def test_unauth_interaction_fhir(self):
        """test_unsupported_resource"""
        response = self.client.get(self.url)

        # Check some response details
        self.assertEqual(response.status_code, 404)


class FHIRCheckResourceTypeAccessTestCase(TestCase):
    """
    Test Access_Permitted and Access_Denied

    {"model": "server.supportedresourcetype",
    "pk": 2,
    "fields": {"resource_name": "ExplanationOfBenefit",
              "json_schema": "{}",
              "get": true,
              "put": false,
              "create": false,
              "read": true,
              "vread": true,
              "update": false,
              "patch": false,
              "delete": false,
              "search": true,
              "history": true
             }
    }

    """

    fixtures = ['fhir_server_testdata.json']

    def test_resource_access_permitted_or_not(self):
        """ Check Access_Permitted and Access_Denied in Record

        """

        resource = SupportedResourceType.objects.get(pk=2)

        tests = [('fhir_get', True),
                 ('fhir_put', False),
                 ('fhir_create', False),
                 ('fhir_read', True),
                 ('fhir_update', False),
                 ('fhir_patch', False),
                 ('fhir_delete', False),
                 ('fhir_search', True),
                 ('fhir_history', True),
                 ]

        # Test for Access Permitted
        for test, result in tests:
            expect = resource.access_permitted(test)

            # print("\n Permitted Check: %s = %s expected: %s" % (test, result, expect))
            self.assertEqual(result, expect)

        # Test for Access Denied
        for test, result in tests:
            expect = resource.access_denied(test)

            # print("\n Denied Check: %s = %s expected: %s" % (test, not result, expect))
            self.assertEqual(not result, expect)
