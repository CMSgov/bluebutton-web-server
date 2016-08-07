#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: rt_practitioner
Created: 8/7/16 12:13 AM

File created by: ''
"""
from collections import OrderedDict
from ..utils.fhir_resource_version import V_DSTU2
from ..utils.utils_fhir_dt import (dt_meta,
                                   dt_human_name,
                                   dt_address)


def build_practitioner_dstu2(practitioner,
                             vid=None,
                             resourceVersion=V_DSTU2):
    """
        build practitioner resource

        http://hl7.org/fhir/2016May/practitioner.html
{
  "resourceType" : "Practitioner",
  // from Resource: id, meta, implicitRules, and language
  // from DomainResource: text, contained, extension, and modifierExtension
  "identifier" : [{ Identifier }], // A identifier for the person as this agent
  "active" : <boolean>, // Whether this practitioner's record is in active use
  "name" : [{ HumanName }], // The name(s) associated with the practitioner
  "telecom" : [{ ContactPoint }], // A contact detail for the practitioner (that apply to all roles)
  "address" : [{ Address }], // Address(es) of the practitioner that are not role specific (typically home address)
  "gender" : "<code>", // male | female | other | unknown
  "birthDate" : "<date>", // The date  on which the practitioner was born
  "photo" : [{ Attachment }], // Image of the person
  "practitionerRole" : [{ // Roles/organizations the practitioner is associated with
    "organization" : { Reference(Organization) }, // Organization where the roles are performed
    "role" : { CodeableConcept }, // Roles which this practitioner may perform
    "specialty" : [{ CodeableConcept }], // Specific specialty of the practitioner
    "identifier" : [{ Identifier }], // Business Identifiers that are specific to a role/location
    "telecom" : [{ ContactPoint }], // Contact details that are specific to the role/location/service
    "period" : { Period }, // The period during which the practitioner is authorized to perform in these role(s)
    "location" : [{ Reference(Location) }], // The location(s) at which this practitioner provides care
    "healthcareService" : [{ Reference(HealthcareService) }] // The list of healthcare
                                                                services that
                                                                this worker
                                                                provides for this
                                                                role's Organization/Location(s)
  }],
  "qualification" : [{ // Qualifications obtained by training and certification
    "identifier" : [{ Identifier }], // An identifier for this qualification for the practitioner
    "code" : { CodeableConcept }, // R!  Coded representation of the qualification
    "period" : { Period }, // Period during which the qualification is valid
    "issuer" : { Reference(Organization) } // Organization that regulates and issues the qualification
  }],
  "communication" : [{ CodeableConcept }] // A language the practitioner is able to use in patient communication
}
    """

    rt = OrderedDict()
    rt['resourceType'] = "Practitioner"

    rt['meta'] = dt_meta(vid,)

    if 'name' in practitioner:
        print("\nPractitioner received:%s" % practitioner)
        rt['name'] = dt_human_name(practitioner['name'])

    if 'telecom' in practitioner:
        rt['telecom'] = practitioner['telecom']

    if 'address' in practitioner:
        rt['address'] = dt_address(practitioner['address'])

    return rt
