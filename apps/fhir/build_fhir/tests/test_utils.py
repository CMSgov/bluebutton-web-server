#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
Project: hhs_oauth_server
App: apps.fhir.build_fhir.tests
FILE: test_utils
Created: 7/28/16 8:17 AM

Created by: Mark Scrimshire @ekivemark
"""

from unittest import TestCase

from ..utils.utils import (get_guid,
                           capitalize_string)


class TestBuild_FHIR_UtilsSimple(TestCase):
    """ Test Utils for Build_FHIR """

    def test_get_guid(self):
        """ Test that GUID is returned """

        resp = get_guid()

        print("\nGuid:%s[%s]" % (resp, len(resp)))
        self.assertEqual(len(resp), 36)

        resp_block = resp.split('-')

        print("\nResp blocks:%s" % len(resp_block))

        self.assertEqual(len(resp_block), 5)