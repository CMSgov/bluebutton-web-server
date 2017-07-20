#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: utils
Created: 10/20/16 11:06 PM

File created by: 'MArk Scrimshire: @ekivemark'
"""

from decimal import Decimal
import platform

TRUE_LIST = [1, "1", "true", "True", "TRUE", "YES", "Yes", "yes", True]
FALSE_LIST = [0, "0", "False", "FALSE", "false", "NO", "No", "no", False]


def bool_env(env_val):
    """ check for boolean values """

    if env_val:
        if env_val in TRUE_LIST:
            return True
        if env_val in FALSE_LIST:
            return False
        # print("Return:%s" % env_val)
        return env_val
    else:
        if env_val in FALSE_LIST:
            return False

        # print("Returning:%s" % env_val)
        return


def int_env(env_val):
    """ convert to integer from String """

    return int(Decimal(float(env_val)))


def is_python2():
    """
        Check if Python 2.x because we need to deal with
        unicode to text conversion for URLfields

    """

    if platform.python_version_tuple()[0] == '2':
        return True
    else:
        return False
