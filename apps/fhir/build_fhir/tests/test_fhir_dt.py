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
# import json

from datetime import datetime
# from pytz import timezone
# from django.conf import settings
from django.utils.timezone import get_current_timezone

from unittest import TestCase

# from apps.fhir.bluebutton.utils import pretty_json

from apps.fhir.build_fhir.utils.utils_fhir_dt import (dt_instant,
                                                      dt_meta,
                                                      dt_codeable_concept,
                                                      dt_coding,
                                                      dt_identifier,
                                                      dt_address,
                                                      dt_period,
                                                      dt_diagnosis,
                                                      dt_money)


class FHIRDataTypeUtilsTest(TestCase):

    def test_dt_instant_default(self):
        """ Create a default FHIR Instant datetime format """

        resp = dt_instant()

        # print("\nNow:", resp)

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

    def test_dt_meta(self):
        """ Test the meta segment - with vid and without """

        format = '%b %d %Y %I:%M%p'
        tz = get_current_timezone()

        now_is = datetime.strptime('Jun 1 2015  1:33PM', format)
        my_now = tz.localize(now_is)

        resp = dt_meta()

        # print("\nMeta:%s" % resp)
        if 'versionId' in resp:
            result = True
            self.assertTrue((result is True))

        resp = dt_meta(vid=2)

        # print("\nMeta:%s" % resp)
        # result = json.loads(resp)
        result = resp

        self.assertEqual(result['versionId'], "2")

        resp = dt_meta(vid="3")

        # print("\nMeta:%s" % resp)
        # result = json.loads(resp)
        result = resp

        self.assertEqual(result['versionId'], "3")

        resp = dt_meta(vid=None, last_updated=my_now)

        # result = json.loads(resp)
        result = resp
        # print("\nResult:%s" % result)

        self.assertEqual(result['lastUpdated'],
                         "2015-06-01T13:33:00+00:00")

    def test_codeable_concept(self):
        """ Test Codeable concept passed as dict, list or string """

        concept = "just a string"

        resp = dt_codeable_concept(concept)

        # print("\nConcept:%s = %s" % (concept, resp))
        # result = json.loads(resp)
        result = resp

        # print("\nJSON:%s" % result)

        self.assertEqual(result['text'], "just a string")

    def test_coding_valid(self):
        """ test Coding data type is correctly constructed """

        coding = "just a string to explain a code"

        resp = dt_coding(coding)
        if resp:
            # result = json.loads(resp)
            result = resp
            # print("\nCoding Result:%s" % result)

        self.assertEqual(resp, None)

        code_dict = {"display": coding}

        resp = dt_coding(code_dict)
        result = {}
        if resp:
            # result = json.loads(resp)
            result = resp
            # print("\nCoding Result:%s" % result)

        self.assertEqual(result['display'], coding)

    def test_coding_valid_full(self):
        """ Test Coding returns a complete coding block """

        coding = {"display": "just a string to explain a code",
                  "system": "http://example.com/code/",
                  "version": "1.0",
                  "code": "<code>",
                  "userSelected": True}

        resp = dt_coding(coding)

        if resp:
            # result = json.loads(resp)
            result = resp
            # print("\nFull Code:%s" % result)
        else:
            result = {}

        self.assertEqual(result['system'], coding['system'])
        self.assertEqual(result['version'], coding['version'])
        self.assertEqual(result['code'], coding['code'])
        self.assertEqual(result['userSelected'], coding['userSelected'])

    def test_address(self):
        """ Test Address Data Type

        """

        address = {}

        resp = dt_address(address)

        # print("\nAddress:%s" % resp)

        self.assertEqual(resp, None)

        address = {}
        resp = dt_address(address, None, None, "123 Fourth Ave")

        # print("\nAddress:%s" % resp)
        # result = json.loads(resp)
        result = resp

        self.assertEqual(result['text'], '123 Fourth Ave')

        address = {"addressLine1": '123 Fourth Ave',
                   "addressLine2": 'Apt 2B',
                   "city": "Baltimore",
                   "state": "MD",
                   "zip": "21148",
                   "period": dt_period(start_date=dt_instant())
                   }

        resp = dt_address(address, "Home", "Both", "123 Fourth Ave")

        # print("\nAddress:%s" % resp)
        # result = json.loads(resp)
        result = resp

        self.assertEqual(result['text'], '123 Fourth Ave')
        self.assertEqual(result['line'], ['123 Fourth Ave', 'Apt 2B'])
        self.assertEqual(result['city'], 'Baltimore')
        self.assertEqual(result['state'], 'MD')
        self.assertEqual(result['postalCode'], "21148")
        self.assertEqual(result['use'], 'home')
        self.assertEqual(result['type'], 'both')

    def test_identifier(self):
        """ Test setting a data type Identifier """

        resp = dt_identifier("123456")

        # result = json.loads(resp)
        result = resp
        # print("\nIdentifier:%s" % result)

        self.assertEqual(result, {"value": "123456"})

        resp = dt_identifier("123456",
                             id_use="OFFICIAL",
                             id_system="http://example.com/")

        # result = json.loads(resp)
        result = resp

        # print("\nIdentifier:%s" % result)

        self.assertEqual(result['value'], "123456")
        self.assertEqual(result['use'], "official")
        self.assertEqual(result['system'], "http://example.com/")

    def test_diagnosis(self):
        """ Test diagnosis dt """

        diag_list = ["V123", "D12345", "E7654"]

        result = dt_diagnosis(diag_list)

        expected = {"sequence": "2",
                    "diagnosis": {"system": "http://hl7.org/fhir/"
                                            "sid/icd-9-cm/diagnosis",
                                  "code": "D12345"}}

        # print("\nDiagnoses:%s" % result)
        self.assertEqual(result[1], expected)

    def test_money(self):
        """ Test Money dataType """

        money = "$100.99"
        result = dt_money(money)

        expected = {"value": 100.99,
                    "system": "urn:std:iso:4217",
                    "code": "USD"}

        # print("\nMoney:%s" % pretty_json(result))

        self.assertEqual(result, expected)
