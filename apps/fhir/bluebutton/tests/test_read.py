try:
    # python 3 - Mock is now a standard module in unittest
    from unittest.mock import Mock, patch
except ImportError:
    # python 2 - Mock needs to be pip installed
    from mock import Mock, patch   # NOQA


# from collections import OrderedDict
import json

import apps.fhir.bluebutton.utils
# from apps.fhir.bluebutton.utils import pretty_json
import apps.fhir.bluebutton.views.home
from apps.fhir.bluebutton.views.home import (conformance_filter)

from django.test import TestCase, RequestFactory

# Get the pre-defined Conformance statement
from .data_conformance import CONFORMANCE
# from .data_conformance_filtered import FILTERED_CONFORMANCE


class ConformanceReadRequestTest(TestCase):
    """ Check the BlueButton API call  """
    def setUp(self):
        # Setup the RequestFactory
        self.factory = RequestFactory()
        self.fixtures = [
            'fhir_server_testdata_prep.json',
            'fhir_bluebutton_test_rt.json'
        ]

    @patch('apps.fhir.bluebutton.utils.requests')
    def test_fhir_bluebutton_read_conformance_testcase(self, mock_requests):
        """ Checking Conformance

            The @patch replaces the call to requests ith mock_requests

        """

        call_to = '/bluebutton/fhir/v1/metadata'
        request = self.factory.get(call_to)

        # Now we can setup the responses we want to the call
        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.text = CONFORMANCE

        # Make the call to request_call which uses requests.get
        # patch will intercept the call to requests.get and
        # return the pre-defined values
        result = apps.fhir.bluebutton.utils.request_call(request,
                                                         call_to,
                                                         fail_redirect="/")

        # Activate the print statement if you want to see what was returned
        # print("\nText:%s" % result.text)

        # Test for a match
        self.assertEqual(result.text, CONFORMANCE)

    @patch('apps.fhir.bluebutton.views.home.get_resource_names')
    def test_fhir_conformance_filter(self, mock_get_resource_names):
        """ Check filtering of Conformance Statement """

        # call_to = '/bluebutton/fhir/v1/metadata'
        # request = self.factory.get(call_to)

        # Now we can setup the responses we want to the call
        mock_get_resource_names.return_value = ['ExplanationOfBenefit',
                                                'Patient']

        conform_out = json.loads(CONFORMANCE)
        result = conformance_filter(conform_out,
                                    "json")

        # print("\nResult from Filter:%s" % pretty_json(result))
        if "vision" in result['rest'][0]['resource']:
            filter_works = False
        else:
            filter_works = True

        self.assertEqual(filter_works, True)
