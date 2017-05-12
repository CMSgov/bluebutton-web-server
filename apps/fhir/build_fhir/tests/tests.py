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
import json
# import requests

from unittest import TestCase

from django.test import RequestFactory
from django.contrib.auth.models import User
from ...testac.tests.test_harness import FakeMessages, MessagingRequest
from ...testac.utils.sample_json_bb import SAMPLE_BB_JSON
from ...testac.utils.sample_json_bb_claim import SAMPLE_BB_CLAIM_PART_A

from ..views.base import build_patient
from ..utils.utils import clean_escape, pretty_json
from ...testac.views.base import fhir_build_patient
# from ...bluebutton.utils import FhirServerUrl
from ..views.rt_explanationofbenefit import build_eob
from ..utils.fhir_resource_version import V_DSTU21, V_DSTU2
from unittest import skip


@skip("Sandbox use only")
class TestBuildPatient(TestCase):
    """ Build a patient resource """

    def test_build_patient(self):
        """ Build a patient resource """

        pre_text = clean_escape(SAMPLE_BB_JSON)
        # print("\npre_text:%s" % pre_text)
        # pt_json = json.loads(pre_text)

        resp = pretty_json(build_patient(pre_text))

        result = json.loads(resp)
        # print("\nBuilt Patient:%s" % pretty_json(result))

        self.assertEqual(result['name']['text'], "JOHN DOE".title())


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


@skip("Sandbox use only")
class TestBuildFHIRPatient(TestCase):
    """ Construct the FHIR Patient Record.

    """

    def setUp(self):
        # Setup the RequestFactory
        # I could probably update this to use a Mock()
        self.factory = RequestFactory()
        self.messages = MessagingRequest()
        self.user = User.objects.create_user(
            username='fred3', email='fred3@...', password='top_secret')

    def test_build_fhir_patient(self):
        request = self.factory.get('/create_test_account/bb_upload/')
        request.user = self.user
        request._messages = FakeMessages()

        result, pt = fhir_build_patient(request,
                                        json.loads(SAMPLE_BB_JSON))

        # print("\nResult:%s" % result)
        self.assertEqual(result.status_code, 201)
        # self.assertEqual(result.status_code, 404)


@skip("Sandbox use only")
class TestWriteFHIRPatient(TestCase):
    """ Write the FHIR Patient Record.

    """

    def setUp(self):
        # Setup the RequestFactory
        # I could probably update this to use a Mock()
        self.factory = RequestFactory()
        self.messages = MessagingRequest()
        self.user = User.objects.create_user(
            username='fred4', email='fred4@...', password='top_secret')

    def test_write_patient(self):
        """ Write to the backend """

        request = self.factory.get('/create_test_account/bb_upload/')
        user = User.objects.create_user(
            username='jacob8', email='jacob8@...', password='top_secret')

        request.user = user
        request._messages = FakeMessages()
        # url = FhirServerUrl() + "Patient"
        # headers = {'content-type': 'application/json'}
        result, pt = fhir_build_patient(request,
                                        json.loads(SAMPLE_BB_JSON))

        # print("\nPayload:%s" % result)

        # print("\nurl: %s" % url)
        # print("\nPatient Write Response"
        #       "(JSON):%s" % pretty_json(result.json()))

        self.assertEqual(result.status_code, 201)
        # self.assertEqual(result.status_code, 404)


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

    def test_construct_default_eob_v21_good(self):
        """ Create an EOB with default version dstu2 """

        patient = "Patient/12345678"
        claim = json.loads(SAMPLE_BB_CLAIM_PART_A)
        version = V_DSTU21

        result = build_eob(patient, claim, version)
        # json_stuff = pretty_json(result)
        expected = "12345678900000VAA"

        # print("\nResult of build_eob:%s" % result)

        self.assertEqual(result['claimIdentifier'], expected)

        patient = None
        claim = json.loads(SAMPLE_BB_CLAIM_PART_A)
        version = V_DSTU21

        result = build_eob(patient, claim, version)
        # json_stuff = pretty_json(result)
        expected = None

        self.assertEqual(result, expected)

        patient = "Patient/12345678"
        claim = None
        version = V_DSTU21

        result = build_eob(patient, claim, version)
        # json_stuff = pretty_json(result)
        expected = None

        self.assertEqual(result, expected)
