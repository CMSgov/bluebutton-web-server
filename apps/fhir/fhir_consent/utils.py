#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: utils
Created: 10/14/16 1:46 AM

File created by: ''
"""


def resource_from_scopes(oauth_permissions):
    """ Extract resource names from permissions/scopes """
    if oauth_permissions:
        if isinstance(oauth_permissions, str):
            o_permissions = [oauth_permissions,]
        else:
            o_permissions = oauth_permissions

        # print("o_permissions: %s\n%s"
        #       "\n#################" % (type(o_permissions),
        #                                o_permissions))
        resource_list = []

        for scope in o_permissions:
            # print("\nScope:%s" % scope)
            if 'code' in scope:
                resource_action = scope['code'].split("/")
            else:
                resource_action = scope.split("/")
            if len(resource_action) > 1:
                resource = resource_action[1].split(".")
            else:
                resource = resource_action
            if resource[0] in resource_list:
                pass
            else:
                resource_list.append(resource[0])
        # print("\nResource List for Consent:\n%s"
        #       "\n####################" % resource_list)
        return resource_list
    else:
        return None


def strip_code_from_scopes(oauth_permissions):
    """ reconstruct list with codes only
    oauth_permissions = [{"code": "patient/Patient.read"},
                             {"code": "patient/ExplanationOfBenefit.read"},
                             {"code": "patient/Consent.*"}]

    converts to:
    oauth_list = ["patient/Patient.read",
                  "patient/ExplanationOfBenefit.read",
                  "patient/Consent.*"]
    """

    resource_list = []

    if oauth_permissions:
        for scope in oauth_permissions:
            resource_action = scope['code']
            if resource_action in resource_list:
                pass
            else:
                resource_list.append(resource_action)
        return resource_list
    else:
        return None
