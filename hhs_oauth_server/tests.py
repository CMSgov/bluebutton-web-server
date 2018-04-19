"""
hhs_oauth_server
FILE: tests
Created: 10/20/16 11:24 PM

File created by: 'Mark Scrimshire: @ekivemark'
"""

from django.test import TestCase
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
