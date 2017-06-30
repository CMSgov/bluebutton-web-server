#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
Project: hhs_oauth_server
App: apps.fhir.build_fhir.tests
FILE: tests
Created: 7/28/16 8:17 AM

Created by: Mark Scrimshire @ekivemark
"""
# import json
# import requests

from unittest import TestCase

from ..utils.utils import clean_escape
# from ...bluebutton.utils import FhirServerUrl
from ..views.rt_explanationofbenefit import build_eob
from ..utils.fhir_resource_version import V_DSTU2


class TestProblemTextReplacement(TestCase):
    """ Deal with Escaped quotes in text  """

    def test_deal_with_problem_text(self):
        """ Fixing escaped quotes in text """
        problem_text = """
{
    "patient": "we have to deal with 'escaped' text in text json",
    "languageCode": "code='en-US'",
    "confidentialityCode": {
        "code": "N",
        "codeSystem": "2.16.840.1.113883.5.25"
        }
}
        """

        resp = clean_escape(problem_text)
        # print("\nResp Type:%s" % (type(resp)))
        # resp = json.dumps(problem_text)
        # print("\nJson.dumps:\n%s" % resp)

        # result = o_json(resp)

        # print("\nloads:%s" % resp)
        # print("Result type:%s" % type(resp))
        self.assertEqual(resp['patient'],
                         "we have to deal with \'escaped\' text in text json")


class TestWriteEOB(TestCase):
    """ Write an EOB Resource """

    def test_construct_default_eob(self):
        """ Create an EOB with default version """

        patient = {}
        claim = {}
        # version = None

        result = build_eob(patient, claim)

        expected = None

        self.assertEqual(result, expected)

    def test_construct_default_eob_v2_bad(self):
        """ Create an EOB with default version dstu2 """

        patient = {}
        claim = {}
        version = V_DSTU2

        result = build_eob(patient, claim, version)

        expected = None

        self.assertEqual(result, expected)
