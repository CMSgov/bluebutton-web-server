#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
Project: ir-fhir
App: apps.api.tests
FILE: test_fhir_dt
Created: 7/24/16 12:45 PM

Created by: Mark Scirmshire @ekivemark, Medyear

Test FHIR data type construction

"""
from datetime import datetime
# from pytz import timezone
# from django.conf import settings
from django.utils.timezone import get_current_timezone

from unittest import TestCase

from apps.fhir.build_fhir.utils.utils_fhir_dt import (dt_instant)


class FHIRDataTypeUtilsTest(TestCase):

    def test_dt_instant_default(self):
        """ Create a default FHIR Instant datetime format """

        resp = dt_instant()

        print("\nNow:", resp)

        self.assertIsNotNone(resp)

    def test_dt_instant_mynow(self):
        """ Create a specific FHIR Instant """

        format = '%b %d %Y %I:%M%p'
        tz = get_current_timezone()

        now_is = datetime.strptime('Jun 1 2015  1:33PM', format)
        my_now = tz.localize(now_is)

        resp = dt_instant(my_now)
        # print("\nResponse:%s" % resp)

        expected = my_now.isoformat()
        # print("\nExpected:%s" % expected)

        self.assertEqual(resp, expected)
