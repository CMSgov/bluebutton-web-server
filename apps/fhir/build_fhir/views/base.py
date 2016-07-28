#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
Project: ir-fhir
App: apps.fhir.build_fhir.views
FILE: base
Created: 7/24/16 12:09 PM

Created by: Mark Scrimshire @ekivemark, Medyear

Construct FHIR Data Type elements

"""
from collections import OrderedDict

from ..utils.utils import get_guid, capitalize_string
from ..utils.utils_fhir_dt import (dt_meta,
                                   dt_identifier,
                                   dt_human_name)


def build_patient(pt_json):
    """ Construct a FHIR Patient Profile

        Receive a json dict

        Build a FHIR Patient

        https://www.hl7.org/fhir/patient.html
{
  "resourceType" : "Patient",
  // from Resource: id, meta, implicitRules, and language
  // from DomainResource: text, contained, extension, and modifierExtension
  "identifier" : [{ Identifier }], // An identifier for this patient
  "active" : <boolean>, // Whether this patient's record is in active use
  "name" : [{ HumanName }], // A name associated with the patient
  "telecom" : [{ ContactPoint }], // A contact detail for the individual
  "gender" : "<code>", // male | female | other | unknown
  "birthDate" : "<date>", // The date of birth for the individual
  // deceased[x]: Indicates if the individual is deceased or not. One of these 2:
  "deceasedBoolean" : <boolean>,
  "deceasedDateTime" : "<dateTime>",
  "address" : [{ Address }], // Addresses for the individual
  "maritalStatus" : { CodeableConcept }, // Marital (civil) status of a patient
  // multipleBirth[x]: Whether patient is part of a multiple birth. One of these 2:
  "multipleBirthBoolean" : <boolean>,
  "multipleBirthInteger" : <integer>,
  "photo" : [{ Attachment }], // Image of the patient
  "contact" : [{ // A contact party (e.g. guardian, partner, friend) for the patient
    "relationship" : [{ CodeableConcept }], // The kind of relationship
    "name" : { HumanName }, // A name associated with the contact person
    "telecom" : [{ ContactPoint }], // A contact detail for the person
    "address" : { Address }, // Address for the contact person
    "gender" : "<code>", // male | female | other | unknown
    "organization" : { Reference(Organization) }, // C? Organization that is associated with the contact
    "period" : { Period } // The period during which this contact person or organization is valid to be contacted relating to this patient
  }],
  "animal" : { // This patient is known to be an animal (non-human)
    "species" : { CodeableConcept }, // R!  E.g. Dog, Cow
    "breed" : { CodeableConcept }, // E.g. Poodle, Angus
    "genderStatus" : { CodeableConcept } // E.g. Neutered, Intact
  },
  "communication" : [{ // A list of Languages which may be used to communicate with the patient about his or her health
    "language" : { CodeableConcept }, // R!  The language which can be used to communicate with the patient about his or her health
    "preferred" : <boolean> // Language preference indicator
  }],
  "careProvider" : [{ Reference(Organization|Practitioner) }], // Patient's nominated primary care provider
  "managingOrganization" : { Reference(Organization) }, // Organization that is the custodian of the patient record
  "link" : [{ // Link to another patient resource that concerns the same actual person
    "other" : { Reference(Patient) }, // R!  The other patient resource that the link refers to
    "type" : "<code>" // R!  replace | refer | seealso - type of link
  }]
}

    """
    rt = OrderedDict()
    rt["resourceType"] = "Patient"

    # Write Meta
    rt["meta"] = dt_meta()

    # Assign GUID for Identifier
    id = get_guid()

    # Write Identifier
    rt["identifier"] = dt_identifier(id,)

    # Format name as proper case.
    id_name = capitalize_string(pt_json["patient"]["name"])

    # Write Name
    name = dt_human_name(id_name=id_name)

    # Write Telecom - Phone

    # WRite Telecom - Email

    # Write birthDate

    # Write Address

