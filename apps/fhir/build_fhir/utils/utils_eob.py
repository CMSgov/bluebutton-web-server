#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: utils_eob
Created: 8/5/16 12:17 PM

File created by: ''
"""
from collections import OrderedDict

from .fhir_resource_version import V_DSTU21
# from ...bluebutton.utils import pretty_json

from .utils_fhir_dt import (dt_meta,
                            dt_identifier,
                            dt_human_name,
                            dt_coding,
                            dt_period,
                            dt_address,
                            date_yymmdd,
                            name_drop_md,
                            address_split)

from ..views.rt_practitioner import build_practitioner_dstu2


def build_eob_v21(patient,
                  bb_claim,
                  vid=None,
                  resourceVersion=V_DSTU21):
    """ Extract data from BB_Claim and prep for EOB

    http://hl7-fhir.github.io/explanationofbenefit.html
{
  "resourceType" : "ExplanationOfBenefit",
  // from Resource: id, meta, implicitRules, and language
  // from DomainResource: text, contained, extension, and modifierExtension
  "identifier" : [{ Identifier }], // Business Identifier
  "status" : "<code>", // R!  active | cancelled | draft | entered-in-error
  // author[x]: Insurer. One of these 2:
  "authorIdentifier" : { Identifier },
  "authorReference" : { Reference(Organization) },
  // claim[x]: Claim reference. One of these 2:
  "claimIdentifier" : { Identifier },
  "claimReference" : { Reference(Claim) },
  // claimResponse[x]: Claim response reference. One of these 2:
  "claimResponseIdentifier" : { Identifier },
  "claimResponseReference" : { Reference(ClaimResponse) },
  "type" : { Coding }, // R!  Type or discipline
  "subType" : [{ Coding }], // Finer grained claim type information
  "ruleset" : { Coding }, // Current specification followed
  "originalRuleset" : { Coding }, // Original specification followed
  "created" : "<dateTime>", // Creation date
  "billablePeriod" : { Period }, // Period for charge submission
  "outcome" : { Coding }, // complete | error | partial
  "disposition" : "<string>", // Disposition Message
  // provider[x]: Responsible provider for the claim. One of these 2:
  "providerIdentifier" : { Identifier },
  "providerReference" : { Reference(Practitioner) },
  // organization[x]: Responsible organization for the claim. One of these 2:
  "organizationIdentifier" : { Identifier },
  "organizationReference" : { Reference(Organization) },
  // facility[x]: Servicing Facility. One of these 2:
  "facilityIdentifier" : { Identifier },
  "facilityReference" : { Reference(Location) },
  "related" : [{ // Related Claims which may be revelant to processing this claimn
    // claim[x]: Reference to the related claim. One of these 2:
    "claimIdentifier" : { Identifier },
    "claimReference" : { Reference(Claim) },
    "relationship" : { Coding }, // How the reference claim is related
    "reference" : { Identifier } // Related file or case reference
  }],
  // prescription[x]: Prescription. One of these 2:
  "prescriptionIdentifier" : { Identifier },
  "prescriptionReference" : { Reference(MedicationOrder|VisionPrescription) },
  // originalPrescription[x]: Original Prescription. One of these 2:
  "originalPrescriptionIdentifier" : { Identifier },
  "originalPrescriptionReference" : { Reference(MedicationOrder) },
  "payee" : { // Payee
    "type" : { Coding }, // Type of party: Subscriber, Provider, other
    "resourceType" : { Coding }, // organization | patient | practitioner | relatedperson
    // party[x]: Party to receive the payable. One of these 2:
    "partyIdentifier" : { Identifier }
    "partyReference" : { Reference(Practitioner|Organization|Patient|RelatedPerson) }
  },
  // referral[x]: Treatment Referral. One of these 2:
  "referralIdentifier" : { Identifier },
  "referralReference" : { Reference(ReferralRequest) },
  "information" : [{ //
    "category" : { Coding }, // R!  Category of information
    "code" : { Coding }, // Type of information
    // timing[x]: When it occurred. One of these 2:
    "timingDate" : "<date>",
    "timingPeriod" : { Period },
    // value[x]: Additional Data. One of these 2:
    "valueString" : "<string>"
    "valueQuantity" : { Quantity }
  }],
  "diagnosis" : [{ // Diagnosis
    "sequence" : "<positiveInt>", // R!  Number to covey order of diagnosis
    "diagnosis" : { Coding }, // R!  Patient's list of diagnosis
    "type" : [{ Coding }], // Type of Diagnosis
    "drg" : { Coding } // Diagnosis Related Group
  }],
  "procedure" : [{ // Procedures performed
    "sequence" : "<positiveInt>", // R!  Procedure sequence for reference
    "date" : "<dateTime>", // When the procedure was performed
    // procedure[x]: Patient's list of procedures performed. One of these 2:
    "procedureCoding" : { Coding }
    "procedureReference" : { Reference(Procedure) }
  }],
  // patient[x]: The subject of the Products and Services. One of these 2:
  "patientIdentifier" : { Identifier },
  "patientReference" : { Reference(Patient) },
  "precedence" : "<positiveInt>", // Precedence (primary, secondary, etc.)
  "coverage" : { // R!  Insurance or medical plan
    // coverage[x]: Insurance information. One of these 2:
    "coverageIdentifier" : { Identifier },
    "coverageReference" : { Reference(Coverage) },
    "preAuthRef" : ["<string>"] // Pre-Authorization/Determination Reference
  },
  "accident" : { //
    "date" : "<date>", // When the accident occurred
    "type" : { Coding }, // The nature of the accident
    // location[x]: Accident Place. One of these 2:
    "locationAddress" : { Address }
    "locationReference" : { Reference(Location) }
  },
  "employmentImpacted" : { Period }, // Period unable to work
  "hospitalization" : { Period }, // Period in hospital
  "item" : [{ // Goods and Services
    "sequence" : "<positiveInt>", // R!  Service instance
    "careTeam" : [{ //
      // provider[x]: . One of these 2:
      "providerIdentifier" : { Identifier },
      "providerReference" : { Reference(Practitioner|Organization) },
      "responsible" : <boolean>, // Billing practitioner
      "role" : { Coding }, // Role on the team
      "qualification" : { Coding } // Type, classification or Specialization
    }],
    "diagnosisLinkId" : ["<positiveInt>"], // Applicable diagnoses
    "revenue" : { Coding }, // Revenue or cost center code
    "category" : { Coding }, // Type of service or product
    "service" : { Coding }, // Billing Code
    "modifier" : [{ Coding }], // Service/Product billing modifiers
    "programCode" : [{ Coding }], // Program specific reason for item inclusion
    // serviced[x]: Date or dates of Service. One of these 2:
    "servicedDate" : "<date>",
    "servicedPeriod" : { Period },
    // location[x]: Place of service. One of these 3:
    "locationCoding" : { Coding },
    "locationAddress" : { Address },
    "locationReference" : { Reference(Location) },
    "quantity" : { Quantity(SimpleQuantity) }, // Count of Products or Services
    "unitPrice" : { Money }, // Fee, charge or cost per point
    "factor" : <decimal>, // Price scaling factor
    "points" : <decimal>, // Difficulty scaling factor
    "net" : { Money }, // Total item cost
    "udi" : [{ Reference(Device) }], // Unique Device Identifier
    "bodySite" : { Coding }, // Service Location
    "subSite" : [{ Coding }], // Service Sub-location
    "noteNumber" : ["<positiveInt>"], // List of note numbers which apply
    "adjudication" : [{ // Adjudication details
      "category" : { Coding }, // R!  Adjudication category such as co-pay, eligible, benefit, etc.
      "reason" : { Coding }, // Adjudication reason
      "amount" : { Money }, // Monetary amount
      "value" : <decimal> // Non-monitory value
    }],
    "detail" : [{ // Additional items
      "sequence" : "<positiveInt>", // R!  Service instance
      "type" : { Coding }, // R!  Group or type of product or service
      "revenue" : { Coding }, // Revenue or cost center code
      "category" : { Coding }, // Type of service or product
      "service" : { Coding }, // Billing Code
      "modifier" : [{ Coding }], // Service/Product billing modifiers
      "programCode" : [{ Coding }], // Program specific reason for item inclusion
      "quantity" : { Quantity(SimpleQuantity) }, // Count of Products or Services
      "unitPrice" : { Money }, // Fee, charge or cost per point
      "factor" : <decimal>, // Price scaling factor
      "points" : <decimal>, // Difficulty scaling factor
      "net" : { Money }, // Total additional item cost
      "udi" : [{ Reference(Device) }], // Unique Device Identifier
      "noteNumber" : ["<positiveInt>"], // List of note numbers which apply
      "adjudication" : [{ Content as for ExplanationOfBenefit.item.adjudication }], // Detail adjudication
      "subDetail" : [{ // Additional items
        "sequence" : "<positiveInt>", // R!  Service instance
        "type" : { Coding }, // R!  Type of product or service
        "revenue" : { Coding }, // Revenue or cost center code
        "category" : { Coding }, // Type of service or product
        "service" : { Coding }, // Billing Code
        "modifier" : [{ Coding }], // Service/Product billing modifiers
        "programCode" : [{ Coding }], // Program specific reason for item inclusion
        "quantity" : { Quantity(SimpleQuantity) }, // Count of Products or Services
        "unitPrice" : { Money }, // Fee, charge or cost per point
        "factor" : <decimal>, // Price scaling factor
        "points" : <decimal>, // Difficulty scaling factor
        "net" : { Money }, // Net additional item cost
        "udi" : [{ Reference(Device) }], // Unique Device Identifier
        "noteNumber" : ["<positiveInt>"], // List of note numbers which apply
        "adjudication" : [{ Content as for ExplanationOfBenefit.item.adjudication }] // SubDetail adjudication
      }]
    }],
    "prosthesis" : { // Prosthetic details
      "initial" : <boolean>, // Is this the initial service
      "priorDate" : "<date>", // Initial service Date
      "priorMaterial" : { Coding } // Prosthetic Material
    }
  }],
  "addItem" : [{ // Insurer added line items
    "sequenceLinkId" : ["<positiveInt>"], // Service instances
    "revenue" : { Coding }, // Revenue or cost center code
    "category" : { Coding }, // Type of service or product
    "service" : { Coding }, // Billing Code
    "modifier" : [{ Coding }], // Service/Product billing modifiers
    "fee" : { Money }, // Professional fee or Product charge
    "noteNumber" : ["<positiveInt>"], // List of note numbers which apply
    "adjudication" : [{ Content as for ExplanationOfBenefit.item.adjudication }], // Added items adjudication
    "detail" : [{ // Added items details
      "revenue" : { Coding }, // Revenue or cost center code
      "category" : { Coding }, // Type of service or product
      "service" : { Coding }, // Billing Code
      "modifier" : [{ Coding }], // Service/Product billing modifiers
      "fee" : { Money }, // Professional fee or Product charge
      "noteNumber" : ["<positiveInt>"], // List of note numbers which apply
      "adjudication" : [{ Content as for ExplanationOfBenefit.item.adjudication }] // Added items detail adjudication
    }]
  }],
  "missingTeeth" : [{ // Only if type = oral
    "tooth" : { Coding }, // R!  Tooth Code
    "reason" : { Coding }, // Reason for missing
    "extractionDate" : "<date>" // Date of Extraction
  }],
  "totalCost" : { Money }, // Total Cost of service from the Claim
  "unallocDeductable" : { Money }, // Unallocated deductable
  "totalBenefit" : { Money }, // Total benefit payable for the Claim
  "payment" : { //
    "type" : { Coding }, // Partial or Complete
    "adjustment" : { Money }, // Payment adjustment for non-Claim issues
    "adjustmentReason" : { Coding }, // Reason for Payment adjustment
    "date" : "<date>", // Expected date of Payment
    "amount" : { Money }, // Payment amount
    "identifier" : { Identifier } // Payment identifier
  },
  "form" : { Coding }, // Printed Form Identifier
  "note" : [{ // Processing notes
    "number" : "<positiveInt>", // Note Number for this note
    "type" : { Coding }, // display | print | printoper
    "text" : "<string>", // Note explanitory text
    "language" : { Coding } // Language
  }],
  "benefitBalance" : [{ // Balance by Benefit Category
    "category" : { Coding }, // R!  Benefit Category
    "subCategory" : { Coding }, // Benefit SubCategory
    "name" : "<string>", // Short name for the benefit
    "description" : "<string>", // Description of the benefit
    "network" : { Coding }, // In or out of network
    "unit" : { Coding }, // Individual or family
    "term" : { Coding }, // Annual or lifetime
    "financial" : [{ // Benefit Summary
      "type" : { Coding }, // R!  Deductable, visits, benefit amount
      // benefit[x]: Benefits allowed. One of these 3:
      "benefitUnsignedInt" : "<unsignedInt>",
      "benefitString" : "<string>",
      "benefitMoney" : { Money },
      // benefitUsed[x]: Benefits used. One of these 2:
      "benefitUsedUnsignedInt" : "<unsignedInt>"
      "benefitUsedMoney" : { Money }
    }]
  }]
}

    """
    if not patient:
        # We have to have a patient ID
        return

    if not bb_claim:
        return

    # We have a claim

    rt = OrderedDict()
    rt['resourceType'] = "ExplanationOfBenefit"
    rt['meta'] = dt_meta(vid=1)

    if 'claimNumber' in bb_claim:
        rt['identifier'] = dt_identifier(bb_claim['claimNumber'])
        rt['claimIdentifier'] = bb_claim['claimNumber']

    if 'claimType' in bb_claim:
        if bb_claim['claimType'] == "PartB":
            coding_dict = {"code": "B",
                           "display": "Part B"}
        elif bb_claim['claimType'] == "Part D":
            coding_dict = {"code": "D",
                           "display": "Part D"}
        else:
            coding_dict = {"code": bb_claim['claimType'],
                           "display": bb_claim['claimType']}
    else:
        coding_dict = {"code": "A",
                       "display": "Part A"}
    rt_type = dt_coding(coding_dict)

    if rt_type:
        rt['type'] = rt_type

    rt['ruleset'] = dt_coding({"code": resourceVersion,
                               "display": resourceVersion})

    if 'date' in bb_claim:
        start_date = date_yymmdd(bb_claim['date']['serviceStartDate'])
        end_date = date_yymmdd(bb_claim['date']['serviceEndDate'])
        rt['billablePeriod'] = dt_period(start_date, end_date)

    if 'provider' in bb_claim:
        if "no information available" not in bb_claim['provider'].lower():
            doc_name = name_drop_md(bb_claim['provider'])
            doc_address = address_split(bb_claim['providerBillingAddress'],
                                        "Billing")
            practitioner = {"name": dt_human_name(doc_name),
                            "address": dt_address(doc_address)}
            rt['providerReference'] = build_practitioner_dstu2(practitioner)

    # Patient ID should be in form Patient/123456
    rt['patientIdentifier'] = patient

    # Return the resourceType
    return rt
