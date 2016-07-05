#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server.apps.eimm
FILE: utils
Created: 7/3/16 10:10 PM

__author__ = 'Mark Scrimshire:@ekivemark'


"""
from collections import OrderedDict


def split_name(in_name=''):
    """ Receive name and break into FHIR HumanName format """

    humanname = OrderedDict()
    humanname['resourceType'] = 'HumanName'
    if in_name == '':
        return humanname

    humanname['text'] = in_name
    name = in_name.rstrip().split(' ')

    humanname['family'] = [name[len(name) - 1]]
    humanname['given'] = []
    ct = 0
    for n in name:
        if ct <= (len(name) - 2):
            humanname['given'].append(n)
        ct += 1

    return humanname
