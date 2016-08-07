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
import json
import uuid

from collections import OrderedDict

from .fhir_code_sets import FHIR_HUMANNAME_USE_CODE

PRETTY_JSON_INDENT = 4


def human_name_use(in_use=None):
    """ Format HumanName use element code

         "use" : "<code>", // usual | official | temp | nickname |
                              anonymous | old | maiden
    """

    return use_code(in_use, FHIR_HUMANNAME_USE_CODE)


def use_code(use=None, code_set=[]):
    """ Validate a code """
    if use:
        if use.lower() in code_set:
            return use.lower()

    return


def build_list_from(field_list=None, id_input=None):
    """ Construct field_list as list """

    if field_list is None:
        if isinstance(id_input, dict):
            for k, v in id_input.items():
                return build_list_from(field_list=k, id_input=v)
        return

    if id_input is None:
        return

    if isinstance(id_input, list):
        return {field_list: id_input}
    else:
        return {field_list: [id_input, ]}


def title_string(in_name=None):
    """ Title Case name """
    if in_name:
        return in_name.title()

    # Nothing received so nothing returned
    return


def get_guid():
    """ get a GUID """

    return str(uuid.uuid4())


def dob_to_fhir(dob=None):
    """ Convert YYYYMMDD to YYYY-MM-DD """
    if not dob:
        return

    str_dob = str(dob)

    return "%s-%s-%s" % (str_dob[:4],
                         str_dob[4:6],
                         str_dob[6:8])


def clean_escape(pre_text):
    """ Need to replace \" with ' in pre_text """

    # patch_text = json.dumps(pre_text)
    # patch_text = pre_text.replace("\"", '"')
    # print("Patch Text:%s" % patch_text)
    return json.loads(pre_text)


def o_json(pre_text):
    """ Convert to OrderedDict """
    if isinstance(pre_text, str):
        # print("\nJSON.loads...")
        return json.loads(json.dumps(pre_text), object_pairs_hook=OrderedDict)
    return


def pretty_json(od, indent=PRETTY_JSON_INDENT):
    """ Print OrderedDict as pretty indented JSON """

    return json.dumps(od, indent=indent)
