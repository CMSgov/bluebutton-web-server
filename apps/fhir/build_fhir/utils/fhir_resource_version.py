#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: fhir_resource_version
Created: 8/5/16 3:29 PM

File created by: ''
"""

V_DEFAULT = "Dstu3"
V_DSTU2 = "Dstu2"
V_DSTU21 = "Dstu2.1"  # Orlando, 2016 Connect-a-thon
V_DSTU3 = "Dstu3"

# FHIR content-type in header is different
FHIR_CONTENT_TYPE_JSON = "application/json+fhir; charset=UTF-8"
FHIR_CONTENT_TYPE_XML = "application/xml+fhir; charset=UTF-8"

# Place Resource_Versions in Alphabetical Order.
# Place Default Version at front of list
# Version list for resource should be sorted in order with newest first
# After default Version
RESOURCE_VERSIONS = [
    {"resourceType": "ExplanationOfBenefit",
     "version": [V_DSTU21, V_DSTU3, ]
     },
    {"resourceType": "Organization",
     "version": [V_DSTU2, ]
     },
    {"resourceType": "Patient",
     "version": [V_DSTU2, ]
     },
    {"resourceType": "Practitioner",
     "version": [V_DSTU2, ]
     },
]


def valid_resource_version(resource=None, version=None):
    """ Check for valid Resource and Version """

    if not resource:
        # print("\nNo Resource")
        return

    rt_to_check = resource.lower()
    # resourceType will get updated by the resource check that follows
    # We have a resource so check it:

    r = check_lower_key_in_dict(rt_to_check,
                                'resourceType',
                                RESOURCE_VERSIONS)

    if not r:
        # Nothing found so return
        # print("\nNo match for %s in %s" % (rt_to_check, RESOURCE_VERSIONS))
        return

    default_version = r['version'][0]
    ver = default_version
    # We have a resource_version
    # Check for version
    if version:
        if version in r['version']:
            ver = version
    # print("\nWe got something:%s" % [r['resourceType'],ver])
    return [r['resourceType'],
            ver]


def check_lower_key_in_dict(rt_to_check, key, list_of_dict):
    """ Iterate through the list of dicts """

    for r in list_of_dict:
        # print("\nR:%s = r[%s]=%s" % (r, key, rt_to_check))
        if rt_to_check.lower() == r[key].lower():
            # print("\nmatched on %s" % rt_to_check)
            return r

    # print("\nFailed to Match [%s]" % rt_to_check)
    return


def valid_resource(resource=None):
    """ Check for Valid Resource """

    if not resource:
        # print("\nNo Resource")
        return

    got_rt = valid_resource_version(resource)

    if not got_rt:
        return

    # We have a resource:
    # print("\nWe got something:%s" % [got_rt[0],got_rt[1])
    # got_rt[resource_type, ver]

    return got_rt[0]


def valid_version_of_resource(resource=None, version=None):
    """ Check for Valid Version for Resource """
    if not version:
        # Nothing to check
        return
    if not resource:
        # print("\nNo Resource")
        return

    r = all_versions_of_resource(resource.lower())

    # print("\nWe got something:%s" % [got_rt[0],got_rt[1])
    # got_rt[resource_type, ver]
    if version in r:
        return version
    else:
        return


def default_version_of_resource(resource=None):
    """ Check for Valid Version for Resource """

    if not resource:
        # print("\nNo Resource")
        return

    got_rt = valid_resource_version(resource)

    if not got_rt:
        return

    # print("\nWe got something:%s" % [got_rt[0],got_rt[1])
    # got_rt[resource_type, ver]

    return got_rt[1]


def all_versions_of_resource(resource=None):
    """ Return the list of versions for a resource """

    if not resource:
        # print("\nNo Resource")
        return

    r = check_lower_key_in_dict(resource.lower(),
                                'resourceType',
                                RESOURCE_VERSIONS)
    # print("\nR = %s" % r)
    if not r:
        return

    # We have something so return list of supported versions
    return r['version']
