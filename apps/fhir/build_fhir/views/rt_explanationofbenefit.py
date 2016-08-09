#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
app: apps.fhir.build_fhir.views
FILE: rt_explanationofbenefit
Created: 8/6/16 12:28 PM

File created by: ''
"""
# from ...bluebutton.utils import pretty_json
from ..utils.utils_eob import build_eob_v21
from ..utils.fhir_resource_version import (default_version_of_resource,
                                           # valid_resource_version,
                                           valid_version_of_resource,
                                           V_DSTU3,
                                           V_DSTU21)


def build_eob(patient, claim, version=None):
    """ Construct an ExplanationOfBenefit Resource """
    resource = 'ExplanationOfBenefit'
    if not version:
        eob_v = default_version_of_resource(resource)
        # print("\nEOB version: %s" % eob_v)

        result = build_eob_dstu21(patient, claim)
        return result

    else:
        eob_v = valid_version_of_resource(resource, version)
        if version == eob_v:
            # print("\nEOB version [%s=%s] is VALID" % (version, eob_v))
            pass
        else:
            # print("\nEOB version [%s=%s] is NOT valid" % (version, eob_v))
            return

    # We have a version specific request to process
    if eob_v == V_DSTU3:
        result = build_eob_dstu3(patient, claim)
        return result
    elif eob_v == V_DSTU21:
        result = build_eob_dstu21(patient, claim)
        return result

    return


def build_eob_dstu3(patient, claim):
    """ Build dstu3 version of EOB """
    version = V_DSTU3
    rt = {}
    print("Generating EOB Version %s" % version)

    return rt


def build_eob_dstu21(patient, claim):
    """ Build dstu3 version of EOB """
    # version = V_DSTU21

    rt = build_eob_v21(patient, claim)
    # print("\nExplanationOfBenefit:\n%s" % rt)
    # print("Generated EOB Version %s" % version)
    # print("\nExplanationOfBenefit:\n%s" % pretty_json(rt))

    return rt
