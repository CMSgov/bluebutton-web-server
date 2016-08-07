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
# import json
from collections import OrderedDict

from ..utils.utils import (get_guid,
                           title_string,
                           dob_to_fhir,
                           pretty_json,
                           use_code,
                           )
from ..utils.utils_fhir_dt import (dt_meta,
                                   dt_identifier,
                                   dt_human_name,
                                   dt_contactpoint,
                                   dt_address)

from ..utils.fhir_code_sets import FHIR_LOCATION_STATUS_CODE


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
    "organization" : { Reference(Organization) }, // C? Organization that is
                                                  // associated with the contact
    "period" : { Period } // The period during which this contact person or
                          // organization is valid to be contacted relating to this patient
  }],
  "animal" : { // This patient is known to be an animal (non-human)
    "species" : { CodeableConcept }, // R!  E.g. Dog, Cow
    "breed" : { CodeableConcept }, // E.g. Poodle, Angus
    "genderStatus" : { CodeableConcept } // E.g. Neutered, Intact
  },
  "communication" : [{ // A list of Languages which may be used to
                       // communicate with the patient about his or her health
    "language" : { CodeableConcept }, // R!  The language which can be used to
                                      // communicate with the patient about his or her health
    "preferred" : <boolean> // Language preference indicator
  }],
  "careProvider" : [{ Reference(Organization|Practitioner) }], // Patient's nominated
                                                               // primary care provider
  "managingOrganization" : { Reference(Organization) }, // Organization that is
                                                        // the custodian of the patient record
  "link" : [{ // Link to another patient resource that concerns the same actual person
    "other" : { Reference(Patient) }, // R!  The other patient resource that the link refers to
    "type" : "<code>" // R!  replace | refer | seealso - type of link
  }]
}
pt_json =
       "address": {
            "addressType": "",
            "addressLine1": "123 ANY ROAD",
            "addressLine2": "",
            "city": "ANYTOWN",
            "state": "VA",
            "zip": "00001"
        },
        "phoneNumber": [
            "123-456-7890"
        ],
        "email": "JOHNDOE@example.com",


    """
    rt = OrderedDict()
    rt["resourceType"] = "Patient"

    # Write Meta
    # rt["meta"] = json.loads(dt_meta())
    rt["meta"] = dt_meta()

    # Assign GUID for Identifier
    id = get_guid()

    # Write Identifier
    # rt["identifier"] = json.loads(dt_identifier(id,))
    rt["identifier"] = dt_identifier(id, )

    # Format name as proper case.
    # print("\nPatient:%s" % pt_json['patient']['name'])

    id_name = title_string(pt_json['patient']['name'])

    # Write Name
    name = dt_human_name(id_name=id_name)
    if name:
        # rt["name"] = json.loads(name)
        rt["name"] = name
    # Write Telecom - Phone
    # phone = json.loads(dt_contactpoint(pt_json['patient']['phoneNumber'],
    #                                    "phone"))
    phone = dt_contactpoint(pt_json['patient']['phoneNumber'], "phone")
    # Write Telecom - Email
    # email = json.loads(dt_contactpoint(pt_json['patient']['email'],
    #                                    "email"))

    email = dt_contactpoint(pt_json['patient']['email'], "email")

    telecom_list = []
    if phone:
        telecom_list.append(phone)
    if email:
        telecom_list.append(email)
    if len(telecom_list) > 0:
        rt['telecom'] = telecom_list
    # Write birthDate
    # "dateOfBirth": "19100101"
    # convert to "yyyy-mm-dd" format
    dob = str(pt_json['patient']['dateOfBirth'])
    if dob:
        rt['birthDate'] = dob_to_fhir(dob)

    # Write Address
    if pt_json['patient']['address']:
        # rt['address'] = json.loads(dt_address(pt_json['patient']['address']))
        rt['address'] = dt_address(pt_json['patient']['address'])

    return rt


def build_location(loc):

    """ format a location resourceType

        https://www.hl7.org/fhir/location.html
{
    "resourceType" : "Location",
      // from Resource: id, meta, implicitRules, and language
      // from DomainResource: text, contained, extension, and modifierExtension
      "identifier" : [{ Identifier }], // Unique code or number identifying the
                                          location to its users
      "status" : "<code>", // active | suspended | inactive
      "name" : "<string>", // Name of the location as used by humans
      "description" : "<string>", // Description of the location
      "mode" : "<code>",  // instance | kind
      "type" : { CodeableConcept },  // Type of function performed
      "telecom" : [{ ContactPoint }], // Contact details of the location
      "address" : { Address }, // Physical location
      "physicalType" : { CodeableConcept }, // Physical form of the location
      "position" : {  // The absolute geographic location
        "longitude" : <decimal>,  // R!  Longitude with WGS84 datum
        "latitude" : <decimal>,  // R!  Latitude with WGS84 datum
        "altitude" : <decimal>  // Altitude with WGS84 datum
      },
      "managingOrganization" : { Reference(Organization) }, // Organization
                                                               responsible for
                                                               provisioning and
                                                               upkeep
      "partOf" : { Reference(Location) } // Another Location this one is
                                            physically part of
}

        """

    rt = OrderedDict()
    rt['resoureType'] = "Location"

    if 'vid' in loc:
        # Write Meta
        # rt["meta"] = json.loads(dt_meta(vid=loc['vid']))
        rt["meta"] = dt_meta(vid=loc['vid'])
    elif 'meta' in loc:
        rt['meta'] = loc['meta']

    if 'identifier' in loc:
        rt['identifier'] = loc['identifier']
    elif 'id_value' in loc:
        rt['identifier'] = dt_identifier(loc['id_value'])

    if 'status' in loc:
        rt['status'] = use_code(loc['status'],
                                code_set=FHIR_LOCATION_STATUS_CODE)

    if 'name' in loc:
        rt['name'] = loc['name']

    if 'address' in loc['address']:
        rt['address'] = loc['address']

    return pretty_json(rt)
