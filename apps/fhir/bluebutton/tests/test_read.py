from unittest.mock import patch
import json
import apps.fhir.bluebutton.utils
import apps.fhir.bluebutton.views.home
from apps.fhir.bluebutton.views.home import (conformance_filter)
from django.test import TestCase, RequestFactory

# Get the pre-defined Conformance statement
from .data_conformance import CONFORMANCE


class ConformanceReadRequestTest(TestCase):
    """ Check the BlueButton API call  """

    # 'fhir_server_testdata_prep.json',
    fixtures = ['fhir_bluebutton_test_rt.json']

    def setUp(self):
        # Setup the RequestFactory
        self.factory = RequestFactory()

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
