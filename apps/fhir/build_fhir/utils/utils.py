#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
Project: hhs_oauth_server
App: apps.fhir.build_fhir.utils
FILE: utils
Created: 7/27/16 9:54 PM

Created by: Mark Scrimshire @ekivemark, Medyear

"""
import uuid

FHIR_HUMANNAME_USE_CODE = ['usual',
                           'official',
                           'temp',
                           'nickname',
                           'anonymous',
                           'old',
                           'maiden']


def humanname_use(in_use=None):
    """ Format HumanName use element code

         "use" : "<code>", // usual | official | temp | nickname |
                              anonymous | old | maiden
    """

    if in_use:
        if in_use.lower() in FHIR_HUMANNAME_USE_CODE:
            return {"use": in_use.lower()}

    return


def build_list_from(field_list=None, id_input=None):
    """ Construct field_list as list """

    if field_list is None:
        return None

    if id_input is None:
        return None

    if isinstance(id_input, list):
        return {field_list : id_input}
    else:
        return {field_list : [id_input,]}


def capitalize_string(in_name):
    """ Capitalize name """

    return in_name.title()


def get_guid():
    """ get a GUID """

    return str(uuid.uuid4())