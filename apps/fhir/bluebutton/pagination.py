#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
Project: bluebutton-web-server
App: apps.fhir.bluebutton
FILE: pagination.py
Created: 7/25/18 2:08 PM

Created by: '@ekivemark'
"""

from .constants import SIZE_PARAMETER_OPTIONS, DEFAULT_PAGE_SIZE
# FHIR Standard Query Parameter first in SIZE_PARAMETER_OPTIONS list


def get_page_size(qp):
    """
    Get count or _count from request.GET passed in as QP
    return the first qp with a valid page size that converts to an int
    or return DEFAULT_PAGE_SIZE
    :param qp:
    :return page_size:
    """

    for page_size_field in SIZE_PARAMETER_OPTIONS:
        if page_size_field in qp:
            if is_int(qp.get(page_size_field)):
                try:
                    # print(qp.get(page_size_field))
                    page_size = int(qp.get(page_size_field, DEFAULT_PAGE_SIZE))
                except ValueError:
                    page_size = -1
            else:
                page_size = -1
            return page_size
    return DEFAULT_PAGE_SIZE


def is_int(var):
    """
    Test value for integer
    :param var:
    :return: True | False
    """
    try:
        int(var)
        return True
    except ValueError:
        return False
