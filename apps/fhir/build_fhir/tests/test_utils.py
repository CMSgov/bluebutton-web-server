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
                           title_string,
                           build_list_from,
                           human_name_use,
                           use_code,
                           dob_to_fhir,
                           # pretty_json
                           )
from ..utils.utils_fhir_dt import (name_drop_md,
                                   address_split,
                                   zipcode_from_text,
                                   rt_cms_organization,
                                   rt_hhs_organization,
                                   rt_organization_minimal,
                                   rt_initialize)


class TestBuild_FHIR_UtilsSimple(TestCase):
    """ Test Utils for Build_FHIR """

    def test_get_guid(self):
        """ Test that GUID is returned """

        resp = get_guid()

        # print("\nGuid:%s[%s]" % (resp, len(resp)))
        self.assertEqual(len(resp), 36)

        resp_block = resp.split('-')

        # print("\nResp blocks:%s" % len(resp_block))

        self.assertEqual(len(resp_block), 5)

    def test_title_string(self):
        """ Test Proper Name Formatting """

        name = ["JOHN DOE", "john doe", "John Peter DOE", "DOE,PETER JOHN"]
        expect = ["John Doe", "John Doe", "John Peter Doe", "Doe,Peter John"]
        ct = 0
        for n in name:

            resp = title_string(n)
            # print("\nName: %s = %s" % (n, resp))

            self.assertEqual(resp, n.title())
            self.assertEqual(resp, expect[ct])
            ct += 1

    def test_title_string_no_input(self):
        """ Test nothing in and nothing out """

        name = None
        resp = title_string()

        if not resp:
            # print("\nNothing to report sir!")
            pass

        self.assertEqual(resp, name, "Nothing in and nothing out")

    def test_build_list_from(self):
        """ Test Building a list  from a string or a list"""

        in_text = "just a string"
        resp = build_list_from("prefix", in_text)

        # print("\nResponse:%s" % resp)

        self.assertEqual(resp, {'prefix': ['just a string']})

        in_text = ["more strings", "as list"]
        resp = build_list_from("suffix", in_text)

        # print("\nResponse:%s" % resp)

        self.assertEqual(resp, {'suffix': in_text})

        in_text = {"another": "just a string"}
        resp = build_list_from(field_list=None, id_input=in_text)

        # print("\nResponse from dict:%s" % resp)
        for k, v in in_text.items():
            # print("\nin_text:%s: [%s]" % (k, v))
            pass

        self.assertEqual(resp, {k: [v]})

        in_text = {"another": ["string", "as list"]}
        resp = build_list_from(field_list=None, id_input=in_text)

        # print("\nResponse from dict:%s" % resp)
        for k, v in in_text.items():
            if isinstance(v, list):
                # print("\nin_text-list:%s: %s" % (k, v))
                self.assertEqual(resp, {k: v})
            else:
                # print("\nin_text-string:%s: [%s]" % (k, v))
                self.assertEqual(resp, {k: [v]})

    def test_human_name_use_in_list(self):
        """ test string is in list """

        in_text = "wrong"
        resp = human_name_use(in_text)

        # print("\nResponse:%s from %s" % (resp, in_text))
        self.assertEqual(resp, None)

        in_text = "WRONG"
        resp = human_name_use(in_text)

        # print("\nResponse:%s from %s" % (resp, in_text))
        self.assertEqual(resp, None)

        in_text = "usual"
        resp = human_name_use(in_text)

        # print("\nResponse:%s from %s" % (resp, in_text))
        self.assertEqual(resp, in_text)

        in_text = "OFFICIAL"
        resp = human_name_use(in_text)

        # print("\nResponse:%s from %s" % (resp, in_text))
        self.assertEqual(resp, in_text.lower())

        in_text = "NickName"
        resp = human_name_use(in_text)

        # print("\nResponse:%s from %s" % (resp, in_text))
        self.assertEqual(resp, in_text.lower())

    def test_use_code(self):
        """ Test use code """

        list_of_codes = ['one', 'two', 'three']
        use = "ONE"

        resp = use_code(use, code_set=list_of_codes)

        # print("\n%s found in %s" % (use, list_of_codes))

        self.assertEqual(resp, 'one')

    def test_dob(self):
        """ transform DOB to birthDate """

        dob = "19961031"

        resp = dob_to_fhir(dob)

        # print("%s to %s" % (dob, resp))

        self.assertEqual(resp, "1996-10-31")

    def test_drop_md_good(self):
        """ Test dropping MD from end of name """

        name = "SHELDON  LOW"

        result = name_drop_md(name)
        expected = "SHELDON  LOW"

        self.assertEqual(result, expected)

        name = "SHELDON  LOW MD"

        result = name_drop_md(name)
        expected = "SHELDON  LOW"

        self.assertEqual(result, expected)

        name = "Sheldon Low MD"

        result = name_drop_md(name)
        expected = "Sheldon Low"

        self.assertEqual(result, expected)

        name = ""
        result = name_drop_md(name)
        expected = None

        self.assertEqual(result, expected)

    def test_zip_from_str(self):
        """ Get ZipCode from end of string """

        address = "PO BOX 619092 ROSEVILLE CA 95661-9092"

        result = zipcode_from_text(address)
        expected = "95661-9092"
        self.assertEqual(result, expected)

        address = "PO BOX 619092 ROSEVILLE CA 95661"

        result = zipcode_from_text(address)
        expected = "95661"
        self.assertEqual(result, expected)

        address = "PO BOX 619092 ROSEVILLE CA"

        result = zipcode_from_text(address)
        expected = None
        self.assertEqual(result, expected)

    def test_address_line_split(self):
        """ Split an address string in to line, city, state, zip """

        address = "PO BOX 619092 ROSEVILLE CA 95661-9092"

        result = address_split(address)
        expected = {"addressType": "Official",
                    "addressLine1": "PO BOX 619092",
                    "city": "ROSEVILLE",
                    "state": "CA",
                    "zip": "95661-9092"}

        self.assertEqual(result, expected)

        address = "PO BOX 619092 ROSEVILLE CA 95661"
        addr_type = "Billing"

        result = address_split(address, addr_type)
        expected = {"addressType": "Billing",
                    "addressLine1": "PO BOX 619092",
                    "city": "ROSEVILLE",
                    "state": "CA",
                    "zip": "95661"}

        self.assertEqual(result, expected)

        address = "123 Anytown, Suite #100 Roseville CA 95661"
        addr_type = "Billing"

        result = address_split(address, addr_type)

        expected = {"addressType": "Billing",
                    "addressLine1": "123 Anytown, Suite #100",
                    "city": "Roseville",
                    "state": "CA",
                    "zip": "95661"}

        self.assertEqual(result, expected)


class ResourceTypeTest(TestCase):
    """ Test Resource Types """

    def test_rt_initialize(self):
        """ Create a resource """

        expect = "Consent"
        result = rt_initialize(expect)

        # print("\nrt_initialize result:%s" % pretty_json(result))

        self.assertEqual(result['resourceType'], expect)

    def test_rt_cms_organization_minimal(self):
        """ Create CMS Resource """

        detail_mode = "minimal"
        expect = "Centers for Medicare and Medicaid Services"
        result = rt_cms_organization(detail_mode)

        # print("\nrt_cms_organization result:%s" % pretty_json(result))

        self.assertEqual(result['identifier'][0]['value'], expect)

    def test_rt_cms_organization_full(self):
        """ create full CMS Resource """

        detail_mode = "full"
        # expect = "Centers for Medicare and Medicaid Services"
        expect_vid = "1"
        result = rt_cms_organization(detail_mode)

        # print("\nrt_cms_organization full result:%s" % pretty_json(result))

        self.assertEqual(result['meta']['versionId'], expect_vid)

    def test_rt_hhs_organization_minimal(self):
        """ Create CMS Resource """

        detail_mode = "minimal"
        expect = "US Department of Health and Human Services"
        result = rt_hhs_organization(detail_mode)

        # print("\nrt_hhs_organization full result:%s" % pretty_json(result))

        self.assertEqual(result['identifier'][0]['value'], expect)

    def test_rt_hhs_organization_full(self):
        """ Create full CMS Resource """

        detail_mode = "full"
        # expect = "US Department of Health and Human Services"
        expect_vid = "1"
        result = rt_hhs_organization(detail_mode)

        # print("\nrt_hhs_organization full result:%s" % pretty_json(result))

        self.assertEqual(result['meta']['versionId'], expect_vid)

    def test_organization_minimal(self):
        """ Create Organization """

        expect = "TestOrganization"
        result = rt_organization_minimal(expect)

        # print("\nrt_organization_minimal result:%s" % pretty_json(result))

        self.assertEqual(result['identifier'][0]['value'], expect)
