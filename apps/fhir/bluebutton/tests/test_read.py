try:
    # python 3
    from unittest.mock import Mock, patch
except ImportError:
    # python 2
    from mock import Mock, patch   # NOQA

import apps.fhir.bluebutton.utils
from django.test import TestCase, RequestFactory

from .data_conformance import CONFORMANCE

# from django.contrib.auth.models import User, Group
# from django.test.client import Client
# from django.core.urlresolvers import reverse
# import responses
# import requests
#
# import unittest
#
# from .data_conformance import CONFORMANCE
#
# from ..views.home import fhir_conformance


class ConformanceReadRequestTest(TestCase):
    """ Check the BlueButton API call  """
    def setUp(self):
        # Setup the RequestFactory
        self.factory = RequestFactory()
        self.fixtures = [
            'fhir_bluebutton_testdata_prep.json',
            'fhir_server_testdata_prep.json',
        ]

    @patch('apps.fhir.bluebutton.utils.requests')
    def test_fhir_bluebutton_read_conformance_testcase(self, mock_requests):
        """ Checking Conformance """

        call_to = '/bluebutton/fhir/v1/metadata'
        request = self.factory.get(call_to)

        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.text = CONFORMANCE
        mock_requests.get.return_value.json = {"field": "My text is here!!!!"}

        result = apps.fhir.bluebutton.utils.request_call(request,
                                                         call_to,
                                                         fail_redirect="/")

        print("\nText:%s" % result.text)

        self.assertEqual(result.text, CONFORMANCE)
