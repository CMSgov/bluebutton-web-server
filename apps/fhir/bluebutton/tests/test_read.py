from unittest.mock import patch
import json
import apps.fhir.bluebutton.utils
import apps.fhir.bluebutton.views.home
from apps.fhir.bluebutton.views.home import (conformance_filter)
from django.test import TestCase, RequestFactory
from apps.test import BaseApiTest
from django.test.client import Client
from django.core.urlresolvers import reverse

# Get the pre-defined Conformance statement
from .data_conformance import CONFORMANCE


class ConformanceReadRequestTest(TestCase):
    """ Check the BlueButton API call  """

    # 'fhir_server_testdata_prep.json',
    fixtures = ['fhir_bluebutton_test_rt.json']

    def setUp(self):
        # Setup the RequestFactory
        self.factory = RequestFactory()
        self.client = Client()

    @patch('apps.fhir.bluebutton.utils.requests')
    def test_fhir_bluebutton_read_conformance_testcase(self, mock_requests):
        """ Checking Conformance

            The @patch replaces the call to requests with mock_requests

        """

        call_to = '/bluebutton/fhir/v1/metadata'
        request = self.factory.get(call_to)

        # Now we can setup the responses we want to the call
        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.content = CONFORMANCE

        # Make the call to request_call which uses requests.get
        # patch will intercept the call to requests.get and
        # return the pre-defined values
        result = apps.fhir.bluebutton.utils.request_call(request,
                                                         call_to,
                                                         cx=None)

        # Test for a match
        self.assertEqual(result._response.content, CONFORMANCE)

    @patch('apps.fhir.bluebutton.views.home.get_resource_names')
    def test_fhir_conformance_filter(self, mock_get_resource_names):
        """ Check filtering of Conformance Statement """

        # Now we can setup the responses we want to the call
        mock_get_resource_names.return_value = ['ExplanationOfBenefit',
                                                'Patient']

        conform_out = json.loads(CONFORMANCE)
        result = conformance_filter(conform_out, None)

        if "vision" in result['rest'][0]['resource']:
            filter_works = False
        else:
            filter_works = True

        self.assertEqual(filter_works, True)


class ThrottleReadRequestTest(BaseApiTest):

    def setUp(self):
        # create read and write capabilities
        self.read_capability = self._create_capability('Read', [])
        self.write_capability = self._create_capability('Write', [])
        # Setup the RequestFactory
        self.client = Client()

    def create_token(self, first_name, last_name):
        passwd = '123456'
        user = self._create_user(first_name,
                                 passwd,
                                 first_name=first_name,
                                 last_name=last_name,
                                 email="%s@%s.net" % (first_name, last_name))
        # create a oauth2 application and add capabilities
        application = self._create_application("%s_%s_test" % (first_name, last_name), user=user)
        application.scope.add(self.read_capability, self.write_capability)
        # get the first access token for the user 'john'
        return self._get_access_token(first_name,
                                      passwd,
                                      application,
                                      scope='read')

    @patch('apps.dot_ext.throttling.TokenRateThrottle.get_rate')
    def test_read_throttle(self,
                           mock_rates):
        mock_rates.return_value = '1/day'
        # create the user
        first_access_token = self.create_token('John', 'Smith')

        response = self.client.get(
            reverse(
                'bb_oauth_fhir_read_or_update_or_delete',
                kwargs={
                    'resource_type': 'Nothing',
                    'resource_id': 12}),
            Authorization="Bearer %s" % (first_access_token))

        self.assertEqual(response.status_code, 404)

        self.assertTrue(response.has_header("X-RateLimit-Limit"))
        self.assertEqual(response.get("X-RateLimit-Limit"), "1")

        self.assertTrue(response.has_header("X-RateLimit-Remaining"))
        self.assertEqual(response.get("X-RateLimit-Remaining"), "0")

        self.assertTrue(response.has_header("X-RateLimit-Reset"))
        # 86400.0 is 24 hours
        self.assertEqual(response.get("X-RateLimit-Reset"), '86400.0')

        response = self.client.get(
            reverse(
                'bb_oauth_fhir_read_or_update_or_delete',
                kwargs={
                    'resource_type': 'Nothing',
                    'resource_id': 12}),
            Authorization="Bearer %s" % (first_access_token))

        self.assertEqual(response.status_code, 429)
        # Assert that the proper headers are in place
        self.assertTrue(response.has_header("X-RateLimit-Limit"))
        self.assertEqual(response.get("X-RateLimit-Limit"), "1")

        self.assertTrue(response.has_header("X-RateLimit-Remaining"))
        self.assertEqual(response.get("X-RateLimit-Remaining"), "0")

        self.assertTrue(response.has_header("X-RateLimit-Reset"))
        # 86400.0 is 24 hours
        self.assertTrue(float(response.get("X-RateLimit-Reset")) < 86400.0)

        self.assertTrue(response.has_header("Retry-After"))
        self.assertEqual(response.get("Retry-After"), "86400")

        # Assert that the search endpoint is also ratelimited
        response = self.client.get(
            reverse(
                'bb_oauth_fhir_search',
                kwargs={
                    'resource_type': 'Nothing'}),
            Authorization="Bearer %s" % (first_access_token))

        self.assertEqual(response.status_code, 429)

        # Assert that another token is not rate limited
        second_access_token = self.create_token('Bob', 'Bobbington')
        self.assertFalse(second_access_token == first_access_token)

        response = self.client.get(
            reverse(
                'bb_oauth_fhir_read_or_update_or_delete',
                kwargs={
                    'resource_type': 'Nothing',
                    'resource_id': 12}),
            Authorization="Bearer %s" % (second_access_token))

        self.assertEqual(response.status_code, 404)
