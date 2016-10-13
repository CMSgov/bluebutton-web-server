#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
Project: ir-fhir
App: apps.fhir.build_fhir.views
FILE: rt_operationoutcome
Created: 8/01/16 12:49 AM

Created by: Mark Scrimshire

"""
from collections import OrderedDict
from ..utils.fhir_code_sets import FHIR_OPERATION_SEVERITY_CODE


def rt_operationoutcome(status):
    """ Construct OperationOutcome ResourceType

{
  "resourceType" : "OperationOutcome",
  // from Resource: id, meta, implicitRules, and language
  // from DomainResource: text, contained, extension, and modifierExtension
  "issue" : [{ // R!  A single issue associated with the action
    "severity" : "<code>", // R!  fatal | error | warning | information
    "code" : "<code>", // R!  Error or warning code
    "details" : { CodeableConcept }, // Additional details about the error
    "diagnostics" : "<string>", // Additional diagnostic information about the issue
    "location" : ["<string>"] // XPath of element(s) related to issue
  }]
}

status  = {"outcome": all_lines['msa']['status_code'],
           "issue": all_lines['qak']['status_code']}

     """
    rt = OrderedDict()
    rt['resourceType'] = "OperationOutcome"

    issue = {}
    if 'severity' in status:
        issue['severity'] = status['severity']
    else:
        issue['severity'] = FHIR_OPERATION_SEVERITY_CODE[0]
    if 'outcome' in status:
        issue['code'] = status['outcome']
    if 'issue' in status:
        issue['diagnostics'] = status['issue']

    rt['issue'] = issue

    # print("\nStatus:%s" % status)
    # print("\nOutcome:%s" % dict(rt))

    return rt
