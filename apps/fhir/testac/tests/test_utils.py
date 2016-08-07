#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
Project: hhs_oauth_server
App: apps.fhir.testac
FILE: test_utils
Created: 7/28/16 8:16 AM

Created by: Mark Scrimshire @ekivemark
"""
import json

from django.test import TestCase
from ..utils.sample_json_bb import SAMPLE_FHIR_CREATE_SUCCESS
from ..utils.utils import get_posted_resource_id


class TestGetCrossWalk(TestCase):
    """ Get the Operation Outcome and find Patient URL """

    def test_getXwalk(self):
        """ Get the operation Outcome and break out patient id """

        outcome = json.loads(SAMPLE_FHIR_CREATE_SUCCESS)
        result = get_posted_resource_id(outcome, 201)

        # print("\nPatient/ID:%s" % result)

        self.assertEqual(result, 'Patient/9334211')
