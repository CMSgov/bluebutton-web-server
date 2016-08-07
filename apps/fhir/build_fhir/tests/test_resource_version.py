#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: test_resource_version
Created: 8/5/16 4:40 PM

File created by: ''
"""
from unittest import TestCase

from ..utils.fhir_resource_version import (valid_resource_version,
                                           valid_resource,
                                           valid_version_of_resource,
                                           default_version_of_resource,
                                           all_versions_of_resource,
                                           # V_DEFAULT,
                                           V_DSTU21,
                                           V_DSTU2,
                                           # V_DSTU3
                                           )


class TestResourceVersion(TestCase):
    """ Test Resource Version """

    def test_resource_no_version(self):
        """ Test valid resource with no version """

        version = None
        resource = "Patient"

        result = valid_resource_version(resource=resource, version=version)

        expected = ['Patient', "Dstu2"]

        # print("\nResourceVersion:%s" % result)

        self.assertEqual(result[0], expected[0])
        self.assertEqual(result[1], expected[1])

    def test_resource_bad(self):
        """ Test bad resource with no version """

        version = None
        resource = "Medication"

        result = valid_resource_version(resource=resource, version=version)

        expected = None

        # print("\nResourceVersion:%s" % result)

        self.assertEqual(result, expected)

    def test_resource_good_with_bad_version(self):
        """ Test good resource with bad version """

        version = "Dstu3"
        resource = "Patient"

        result = valid_resource_version(resource=resource, version=version)

        expected = ["Patient", "Dstu2"]

        # print("\nResourceVersion:%s" % result)

        self.assertEqual(result[0], expected[0])
        self.assertEqual(result[1], expected[1])

    def test_resource_good_with_good_version(self):
        """ Test good resource with good version """

        version = "Dstu3"
        resource = "ExplanationOfBenefit"

        result = valid_resource_version(resource=resource, version=version)

        expected = [resource, version]

        # print("\nResourceVersion:%s" % result)

        self.assertEqual(result[0], expected[0])
        self.assertEqual(result[1], expected[1])

    def test_resource_only_good(self):
        """ Test for good resourceType """

        resource = "ExplanationOfBenefit"
        result = valid_resource(resource)

        expected = "ExplanationOfBenefit"

        # print("\nResult: %s = %s" % (result, expected))

        self.assertEqual(result, expected)

        result = valid_resource(resource.lower())

        # print("\nResult: %s = %s" % (result, expected))
        self.assertEqual(result, expected)

        result = valid_resource(resource.upper())

        # print("\nResult: %s = %s" % (result, expected))
        self.assertEqual(result, expected)

    def test_resource_only_bad(self):
        """ Test with a bad resource """

        resource = "UnknownResource"
        result = valid_resource(resource)

        expected = None

        # print("\nResult: %s = %s" % (result, expected))

        self.assertEqual(result, expected)

    def test_version_only_good(self):
        """ Test for good version of resourceType """

        resource = "ExplanationOfBenefit"
        version = "Dstu2.1"
        result = valid_version_of_resource(resource, version)

        expected = "Dstu2.1"

        # print("\nResult: %s = %s" % (result, expected))

        self.assertEqual(result, expected)

    def test_version_only_bad(self):
        """ Test for good resourceType with bad version  """

        resource = "ExplanationOfBenefit"
        version = "Dstu2"
        result = valid_version_of_resource(resource, version)

        expected = None

        # print("\nResult: %s = %s" % (result, expected))

        self.assertEqual(result, expected)

    def test_version_good_default(self):
        """ Test for Default Version of Resource """

        resource = "ExplanationOfBenefit"
        expected = V_DSTU21

        result = default_version_of_resource(resource)

        self.assertEqual(result, expected)

        resource = "organization"

        expected = V_DSTU2

        result = default_version_of_resource(resource)

        self.assertEqual(result, expected)

    def test_all_versions_good_resource(self):
        """ Get list of all versions for a resource """

        resource = "ExplanationOfBenefit"
        expected = ["Dstu2.1", "Dstu3"]

        result = all_versions_of_resource(resource)

        self.assertEqual(result, expected)
