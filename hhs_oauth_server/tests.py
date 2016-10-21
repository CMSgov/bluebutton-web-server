#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: tests
Created: 10/20/16 11:24 PM

File created by: 'Mark Scrimshire: @ekivemark'
"""

from django.test import TestCase
from .utils import bool_env, TRUE_LIST, FALSE_LIST


class Check_BooleanVariable_Test(TestCase):
    """ Check Boolean Variable is converted to Boolean """
    def test_positive_values(self):
        """ test positive values are converted  to True """

        for x in TRUE_LIST:
            expect = True
            result = bool_env(x)
            # print("%s is %s" % (x, expect))
            self.assertEqual(result, expect)

    def test_negative_values(self):
        """ test negative values are converted  to False """

        for y in FALSE_LIST:
            expect = False
            result = bool_env(y)
            # print("%s=%s" % (y, expect))
            self.assertEqual(result, expect)
