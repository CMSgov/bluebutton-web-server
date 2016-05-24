#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: apps.fhir.bluebutton.tests.test_utils
Created: 5/24/16 9:29 AM

run with

python manage.py test apps.fhir.bluebutton.tests.test_utils

"""
__author__ = 'Mark Scrimshire:@ekivemark'

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.conf import settings

import base64
import json
import logging

logger = logging.getLogger('tests.%s' % __name__)

from apps.fhir.bluebutton.utils import notNone

ENCODED = settings.ENCODING


class bluebutton_utils_simple_TestCase(TestCase):
    def test_notNone(self):
        """ Test notNone return values """

        response = notNone("MATCH", "MATCH")
        logger.debug("Testing Response:%s" % response)
        self.assertEqual(response, "MATCH")

        # Empty is not NONE
        response = notNone("", "MATCH")
        logger.debug("Testing Response:%s" % response)
        self.assertNotEqual(response, "MATCH")

        # None returns "Default"
        response = notNone(None, "Default")
        logger.debug("Testing Response:%s" % response)
        self.assertEqual(response, "Default")

        # No values
        response = notNone()
        logger.debug("Testing Response:%s" % response)
        self.assertEqual(response, None)

        # No Default supplied - None Returns None
        response = notNone(None)
        logger.debug("Testing Response:%s" % response)
        self.assertEqual(response, None)

        # No Default supplied - Match Returns Match
        response = notNone("Match")
        logger.debug("Testing Response:%s" % response)
        self.assertEqual(response, "Match")

        # 1 returns 1
        value = 1
        response = notNone(value, "number")
        logger.debug("Testing Response:%s" % response)
        self.assertEqual(response, 1)

        # undefined returns default
        undefinedvalue = None
        response = notNone(undefinedvalue, "default")
        logger.debug("Testing Response:%s" % response)
        self.assertEqual(response, "default")

        # List returns list
        listing = [1,2,3]
        response = notNone(listing, "number")
        logger.debug("Testing Response:%s" % response)
        self.assertEqual(response, listing)

