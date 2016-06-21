#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: test_read
Created: 5/22/16 9:26 PM


"""
from django.test import TestCase, RequestFactory

__author__ = 'Mark Scrimshire:@ekivemark'


class BlueButtonReadRequestTest(TestCase):

    def setUp(self):
        # Setup the RequestFactory
        self.factory = RequestFactory()

        fixtures = ['fhir_bluebutton_testdata_prep.json',
                    'fhir_server_testdata_prep.json']

    def fhir_bluebutton_read_testcase(self):
        """ Patient Not Allowed - No Crosswalk """

        request = self.factory.get('/bluebutton/fhir/v1/Patient')
