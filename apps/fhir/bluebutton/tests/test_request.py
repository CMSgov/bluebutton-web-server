#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: test_request
Created: 4/10/17 2:39 PM

File created by: ''
"""
# import json
import unittest
try:
    # python 3 - Mock is now a standard module in unittest
    from unittest.mock import patch
    from unittest import mock as U_mock
except ImportError:
    # python 2 - Mock needs to be pip installed
    from mock import patch   # NOQA
    import mock as U_mock

from django.test import RequestFactory

# from apps.fhir.bluebutton.utils import (request_call, handle_http_error)

from .data_conformance import CONFORMANCE


class CustomHTTPException(Exception):
    pass


class RC_TestCase(unittest.TestCase):

    def setup(self):
        # Setup the RequestFactory
        self.factory = RequestFactory()

    @U_mock.patch('apps.fhir.bluebutton.utils.handle_http_error')
    @U_mock.patch('apps.fhir.bluebutton.utils.requests.get')
    def test_get_ok(self, mock_get):
        """
        Test getting a 200 OK response from the _get method of request_call.
        """
        # Construct the mock response object, giving it relevant expected
        # behaviours
        mock_response = U_mock.Mock()
        expected_dict = CONFORMANCE
        mock_response.json.return_value = expected_dict

        # Assign mock response as the result of patched request.get function
        mock_get.return_value = mock_response

        # Make our patched error handler raise a custom exception
        # mock_http_error_handler.side_effect = CustomHTTPException()
