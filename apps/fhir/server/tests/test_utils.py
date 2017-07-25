#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: test_utils
Created: 7/21/17 11:31 AM

File created by: '@ekivemark'
"""

from django.test import TestCase

from apps.fhir.server.utils import (search_add_to_list,
                                    payload_additions,
                                    payload_var_replace)


class ServerSearchAddToList(TestCase):
    def test_empty_list(self):
        """ Check for empty text """

        # Test 1: Empty string, return empty dict
        param_string = ''
        response = search_add_to_list(param_string)
        expected = {}
        self.assertEquals(response, expected)

    def test_no_comma_in_list(self):
        # Test 2: no comma in params
        param_string = '_info=specific'
        response = search_add_to_list(param_string)
        expected = {'_info': 'specific'}
        self.assertEquals(response, expected)

    def test_with_comma_in_list(self):
        # Test 3: comman in list
        param_string = 'patient=%PATIENT%,_info=specific'
        response = search_add_to_list(param_string)
        expected = {'patient': '%PATIENT%',
                    '_info': 'specific'}

        # print("\nSearchAddToList Test 3 Response:%s\n" % response)
        self.assertEquals(response, expected)


class ServerPayloadAdditions(TestCase):
    """
    Test adding a dict to the payload
    """

    def test_empty_payload_and_additions(self):
        # Test 1: payload empty and additions empty

        response = payload_additions({})

        self.assertEquals(response, {})

    def test_empty_payload(self):
        # Test 2: Empty payload

        additions = {'_id': "1234"}
        payload = {}

        response = payload_additions(payload, additions)

        self.assertEqual(response, additions)

    def test_empty_additions(self):
        # Test 3: Empty additions

        payload = {'_id': "1234"}
        additions = {}

        response = payload_additions(payload, additions)

        self.assertEqual(response, payload)

    def test_payload_additions(self):
        # Test 4: Add to payload

        payload = {'_id': "1234"}
        additions = {'patient': '%PATIENT%'}

        response = payload_additions(payload, additions)

        self.assertEqual(response, payload)


class ServerPayloadVarReplace(TestCase):
    """
    Test replacing a value in the payload
    """

    def test_empty_payload(self):
        # Test 1: Nothing passed
        response = payload_var_replace()

        self.assertEqual(response, None)

    def test_empty_key(self):
        # Test 2: Empty key

        payload = {'id': 1234}

        response = payload_var_replace(payload)

        self.assertEqual(response, payload)

    def test_payload_key_not_found(self):
        # Test 3: Valid key and matching old_value with no new_value
        payload = {'id': '1234', 'patient': 'oldvalue'}
        key = 'patient'
        old_value = 'oldvalue'

        response = payload_var_replace(payload,
                                       key,
                                       new_value=None,
                                       old_value=old_value)

        expected = {'id': '1234'}

        self.assertEqual(response, expected)

    def test_payload_match_old_value(self):
        # Test 4: Match old_value and replace with new_value
        payload = {'id': '1234', 'patient': 'oldvalue'}
        key = 'patient'
        old_value = 'oldvalue'
        new_value = 'newvalue'

        response = payload_var_replace(payload,
                                       key,
                                       new_value=new_value,
                                       old_value=old_value)

        expected = {'id': '1234', 'patient': 'newvalue'}

        self.assertEqual(response, expected)

    def test_payload_fail_old_value_match(self):
        # Test 5: old value doesn't match so don't replace

        payload = {'id': '1234', 'patient': 'oldestvalue'}
        key = 'patient'
        old_value = 'oldvalue'
        new_value = 'newvalue'

        response = payload_var_replace(payload,
                                       key,
                                       new_value=new_value,
                                       old_value=old_value)

        expected = payload

        # Should be Unchanged
        self.assertEqual(response, expected)
