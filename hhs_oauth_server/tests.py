"""
hhs_oauth_server
FILE: tests
Created: 10/20/16 11:24 PM

File created by: 'Mark Scrimshire: @ekivemark'
"""

from django.test import TestCase
from django.test.client import Client
from django.urls import reverse
import json
from apps.logging.sensitive_logging_filters import mask_mbi


from .utils import bool_env, TRUE_LIST, FALSE_LIST, int_env


class Check_BooleanVariable_Test(TestCase):
    """ Check Boolean Variable is converted to Boolean """
    def test_positive_values(self):
        """ test positive values are converted  to True """

        for x in TRUE_LIST:
            expect = True
            result = bool_env(x)
            self.assertEqual(result, expect)

    def test_negative_values(self):
        """ test negative values are converted  to False """

        for y in FALSE_LIST:
            expect = False
            result = bool_env(y)
            self.assertEqual(result, expect)


class Check_IntFromText_Test(TestCase):
    """ Check that text gets converted to Int """

    def test_int_values(self):
        """ Check we get integers """

        int_list = [("1", 1),
                    ("0", 0),
                    ("10", 10),
                    ("12.123", 12),
                    ("0.49", 0),
                    ("1000000000001", 1000000000001)]

        for x, y in int_list:
            result = int_env(x)
            self.assertEqual(result, y)


class MBI_tests(TestCase):

    def test_mbi_match_dict(self):
        valid_mbi = "1EG4-TE5-MK74"

        my_dict = {
            'key1': valid_mbi,
            'key2': {
                'key4': valid_mbi
            },
            'key3': (valid_mbi, valid_mbi),
            'key5': [valid_mbi, valid_mbi]
        }

        masked_mbi_dict = mask_mbi(my_dict)
        masked_mbi_string = str(masked_mbi_dict)
        self.assertIn('***MBI***', masked_mbi_string)
        self.assertNotIn(valid_mbi, masked_mbi_string)

        mbi_list = [valid_mbi, valid_mbi]
        masked_mbi_list = mask_mbi(mbi_list)
        self.assertIn('***MBI***', masked_mbi_list)
        self.assertNotIn(valid_mbi, masked_mbi_list)

        mbi_tuple = (valid_mbi, valid_mbi)
        masked_mbi_tuple = mask_mbi(mbi_tuple)
        self.assertIn('***MBI***', masked_mbi_tuple)
        self.assertNotIn(valid_mbi, masked_mbi_tuple)

    def test_mbi_match(self):

        mbi_test_list = [
            # Valid MBI
            ("1EG4-TE5-MK74", True),

            # Valid MBI Position 3 as 0
            # Position 3 – alpha-numeric values 0 thru 9and A thru Z (minus S, L, O, I, B, Z)
            ("1E04-TE5-MK74", True),

            # Valid MBI Position 4 as 0
            # Position 4 – numeric values 0 thru 9
            ("1EG0-TE5-MK74", True),

            # Valid MBI Position 6 as 0
            # Position 6 – alpha-numeric values 0 thru 9and A thru Z (minus S, L, O, I, B, Z)
            ("1EG4-T05-MK74", True),

            # Valid MBI Position 7 as 0
            # Position 7 – numeric values 0 thru 9
            ("1EG4-TE0-MK74", True),

            # Valid MBI Position 10 as 0
            # Position 10 – numeric values 0 thru 9
            ("1EG4-TE5-MK04", True),

            # Valid MBI Position 11 as 0
            # Position 11 – numeric values 0 thru 9
            ("1EG4-TE5-MK70", True),


            # Position 1 is invalid
            # Position 1 – numeric values 1 thru 9
            ("AEG4-TE5-MK74", False),

            # Position 2 is invalid
            # P osition 2 – alphabetic values A thru Z (minus S, L, O, I, B, Z)
            ("1SG4-TE5-MK74", False),
            ("1LG4-TE5-MK74", False),
            ("1OG4-TE5-MK74", False),
            ("1IG4-TE5-MK74", False),
            ("1BG4-TE5-MK74", False),
            ("1ZG4-TE5-MK74", False),
            ("11G4-TE5-MK74", False),

            # Position 3 is invalid
            # Position 3 – alpha-numeric values 0 thru 9and A thru Z (minus S, L, O, I, B, Z)
            ("1ES4-TE5-MK74", False),
            ("1EL4-TE5-MK74", False),
            ("1EO4-TE5-MK74", False),
            ("1EI4-TE5-MK74", False),
            ("1EB4-TE5-MK74", False),
            ("1EZ4-TE5-MK74", False),

            # Position 4 is invalid
            # Position 4 – numeric values 0 thru 9
            ("1EGA-TE5-MK74", False),

            # Position 5 is invalid
            # Position 5 – alphabetic values A thru Z (minus S, L, O, I, B, Z)
            ("1EG4-1E5-MK74", False),
            ("1EG4-SE5-MK74", False),
            ("1EG4-LE5-MK74", False),
            ("1EG4-OE5-MK74", False),
            ("1EG4-IE5-MK74", False),
            ("1EG4-BE5-MK74", False),
            ("1EG4-ZE5-MK74", False),

            # Position 6 is invalid
            # Position 6 – alpha-numeric values 0 thru 9and A thru Z (minus S, L, O, I, B, Z)
            ("1EG4-TS5-MK74", False),
            ("1EG4-TL5-MK74", False),
            ("1EG4-TO5-MK74", False),
            ("1EG4-TI5-MK74", False),
            ("1EG4-TB5-MK74", False),
            ("1EG4-TZ5-MK74", False),

            # Position 7 is invalid
            # Position 7 – numeric values 0 thru 9
            ("1EG4-TEA-MK74", False),

            # Position 8 is invalid
            # Position 8 – alphabetic values A thru Z (minus S, L, O, I, B, Z)
            ("1EG4-TE5-1K74", False),
            ("1EG4-TE5-SK74", False),
            ("1EG4-TE5-LK74", False),
            ("1EG4-TE5-OK74", False),
            ("1EG4-TE5-IK74", False),
            ("1EG4-TE5-BK74", False),
            ("1EG4-TE5-ZK74", False),

            # Position 9 is invalid
            # Position 9 – alphabetic values A thru Z (minus S, L, O, I, B, Z)
            ("1EG4-TE5-M174", False),
            ("1EG4-TE5-MS74", False),
            ("1EG4-TE5-ML74", False),
            ("1EG4-TE5-MO74", False),
            ("1EG4-TE5-MOI74", False),
            ("1EG4-TE5-MKB4", False),
            ("1EG4-TE5-MKZ4", False),

            # Position 10 is invalid
            # Position 10 – numeric values 0 thru 9
            ("1EG4-TE5-MKA4", False),

            # Position 11 is invalid
            # Position 11 – numeric values 0 thru 9
            ("1EG4-TE5-MK7A", False),

            # WITHOUT HYPHEN MBI TEST CASES BELOW
            # Valid MBI
            ("1EG4TE5MK74", True),

            # Valid MBI Position 3 as 0
            # Position 3 – alphanumeric values 0 thru 9and A thru Z (minus S, L, O, I, B, Z)
            ("1E04TE5MK74", True),

            # Valid MBI Position 4 as 0
            # Position 4 – numeric values 0 thru 9
            ("1EG0TE5MK74", True),

            # Valid MBI Position 6 as 0
            # Position 6 – alphanumeric values 0 thru 9and A thru Z (minus S, L, O, I, B, Z)
            ("1EG4T05MK74", True),

            # Valid MBI Position 7 as 0
            # Position 7 – numeric values 0 thru 9
            ("1EG4TE0MK74", True),

            # Valid MBI Position 10 as 0
            # Position 10 – numeric values 0 thru 9
            ("1EG4TE5MK04", True),

            # Valid MBI Position 11 as 0
            # Position 11 – numeric values 0 thru 9
            ("1EG4TE5MK70", True),


            # Position 1 is invalid
            # Position 1 – numeric values 1 thru 9
            ("AEG4TE5MK74", False),

            # Position 2 is invalid
            # P osition 2 – alphabetic values A thru Z (minus S, L, O, I, B, Z)
            ("1SG4TE5MK74", False),
            ("1LG4TE5MK74", False),
            ("1OG4TE5MK74", False),
            ("1IG4TE5MK74", False),
            ("1BG4TE5MK74", False),
            ("1ZG4TE5MK74", False),
            ("11G4TE5MK74", False),

            # Position 3 is invalid
            # Position 3 – alphanumeric values 0 thru 9and A thru Z (minus S, L, O, I, B, Z)
            ("1ES4TE5MK74", False),
            ("1EL4TE5MK74", False),
            ("1EO4TE5MK74", False),
            ("1EI4TE5MK74", False),
            ("1EB4TE5MK74", False),
            ("1EZ4TE5MK74", False),

            # Position 4 is invalid
            # Position 4 – numeric values 0 thru 9
            ("1EGATE5MK74", False),

            # Position 5 is invalid
            # Position 5 – alphabetic values A thru Z (minus S, L, O, I, B, Z)
            ("1EG41E5MK74", False),
            ("1EG4SE5MK74", False),
            ("1EG4LE5MK74", False),
            ("1EG4OE5MK74", False),
            ("1EG4IE5MK74", False),
            ("1EG4BE5MK74", False),
            ("1EG4ZE5MK74", False),

            # Position 6 is invalid
            # Position 6 – alphanumeric values 0 thru 9and A thru Z (minus S, L, O, I, B, Z)
            ("1EG4TS5MK74", False),
            ("1EG4TL5MK74", False),
            ("1EG4TO5MK74", False),
            ("1EG4TI5MK74", False),
            ("1EG4TB5MK74", False),
            ("1EG4TZ5MK74", False),

            # Position 7 is invalid
            # Position 7 – numeric values 0 thru 9
            ("1EG4TEAMK74", False),

            # Position 8 is invalid
            # Position 8 – alphabetic values A thru Z (minus S, L, O, I, B, Z)
            ("1EG4TE51K74", False),
            ("1EG4TE5SK74", False),
            ("1EG4TE5LK74", False),
            ("1EG4TE5OK74", False),
            ("1EG4TE5IK74", False),
            ("1EG4TE5BK74", False),
            ("1EG4TE5ZK74", False),

            # Position 9 is invalid
            # Position 9 – alphabetic values A thru Z (minus S, L, O, I, B, Z)
            ("1EG4TE5M174", False),
            ("1EG4TE5MS74", False),
            ("1EG4TE5ML74", False),
            ("1EG4TE5MO74", False),
            ("1EG4TE5MOI74", False),
            ("1EG4TE5MKB4", False),
            ("1EG4TE5MKZ4", False),

            # Position 10 is invalid
            # Position 10 – numeric values 0 thru 9
            ("1EG4TE5MKA4", False),

            # Position 11 is invalid
            # Position 11 – numeric values 0 thru 9
            ("1EG4TE5MK7A", False),
        ]

        for mbi_value, expected in mbi_test_list:
            # Create a text that contains the MBI
            uppercase_mbi_text = f"This is a test string with MBI: {mbi_value}, expected: {expected}."
            masked_uppercase_text = mask_mbi(uppercase_mbi_text)
            lowercase_mbi_text = uppercase_mbi_text.lower()
            masked_mbi_lowercase_text = mask_mbi(lowercase_mbi_text)
            # Check if the MBI was masked
            if expected:
                self.assertIn('***MBI***', masked_uppercase_text)
                self.assertIn('***MBI***', masked_mbi_lowercase_text)
                self.assertNotIn(mbi_value, masked_uppercase_text)
                self.assertNotIn(mbi_value.lower(), masked_mbi_lowercase_text)
            else:
                self.assertNotIn('***MBI***', masked_uppercase_text)
                self.assertNotIn('***MBI***', masked_mbi_lowercase_text)
                self.assertIn(mbi_value, masked_uppercase_text)
                self.assertIn(mbi_value.lower(), masked_mbi_lowercase_text)


class SmartConfigurationTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.smart_url = reverse('smart_configuration')

    def test_valid_smart_config_response(self):
        CAPABILITIES = [
            "client-confidential-symmetric",
            "context-standalone-patient",
            "launch-standalone",
            "permission-offline",
            "permission-patient",
            "permission-v1",
            "permission-v2",
            "authorize-post"
        ]

        SCOPES_SUPPORTED = [
            "openid",
            "profile",
            "launch/patient",
            "patient/Patient.read",
            "patient/ExplanationOfBenefit.read",
            "patient/Coverage.read",
            "patient/Patient.rs",
            "patient/ExplanationOfBenefit.rs",
            "patient/Coverage.rs",
        ]
        response = self.client.get(self.smart_url)
        response_json = response.json()
        response_content = response.content
        response_content = str(response_content, encoding='utf8')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(type(json.loads(response_content)), type({}))
        self.assertCountEqual(response_json['capabilities'], CAPABILITIES)
        self.assertCountEqual(response_json['scopes_supported'], SCOPES_SUPPORTED)
