#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: test_home
Created: 7/19/16 9:04 AM

File created by: ''
"""
from django.test import TestCase, RequestFactory


class BlueButtonReadRequestTest(TestCase):

    def setUp(self):
        # Setup the RequestFactory
        self.factory = RequestFactory()
        self.fixtures = [
            'fhir_server_testdata_prep.json',
        ]


class ConformanceFilterTest(TestCase):
    """ Test that Conformance Statement is filtered """

    # TODO: Write a test using Patient as supported resource.

    # Setup Patient in Supported Resource

    # Make call to Conformance Statement

    # Test that Patient is only resource displayed
