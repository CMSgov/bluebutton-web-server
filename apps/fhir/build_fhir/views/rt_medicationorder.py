#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
apps.fhir.build_fhir.views
FILE: rt_medicationorder
Created: 8/7/16 10:42 PM

File created by: Mark Scrimshire @ekivemark
"""
from collections import OrderedDict

from ..views.base import build_patient
from ..utils.utils_fhir_dt import (dt_meta,
                                   dt_identifier,
                                   # dt_instant,
                                   dt_coding,
                                   dt_codeable_concept,
                                   date_yymmdd)


def rt_medicationorder(partd, patient):
    """ Build MedicationOrder Resource

        partd = bb_claim

        http://hl7-fhir.github.io/medicationorder.html#MedicationOrder

{
  "resourceType" : "MedicationOrder",
  // from Resource: id, meta, implicitRules, and language
  // from DomainResource: text, contained, extension, and modifierExtension
  "identifier" : [{ Identifier }], // External identifier
  "status" : "<code>", // active | on-hold | completed | entered-in-error | stopped | draft
  // medication[x]: Medication to be taken. One of these 2:
  "medicationCodeableConcept" : { CodeableConcept },
  "medicationReference" : { Reference(Medication) },
  "patient" : { Reference(Patient) }, // Who prescription is for
  "encounter" : { Reference(Encounter) }, // Created during encounter/admission/stay
  "dateWritten" : "<dateTime>", // When prescription was initially authorized
  "prescriber" : { Reference(Practitioner) }, // Who ordered the initial medication(s)
  "reasonCode" : [{ CodeableConcept }], // Reason or indication for writing the prescription
  "reasonReference" : [{ Reference(Condition) }], // Condition that supports why the prescription is being written
  "note" : [{ Annotation }], // Information about the prescription
  "category" : "<code>", // Type of medication usage
  "dosageInstruction" : [{ // How medication should be taken
    "text" : "<string>", // Free text dosage instructions e.g. SIG
    "additionalInstructions" : [{ CodeableConcept }], // Supplemental instructions - e.g. "with meals"
    "timing" : { Timing }, // When medication should be administered
    // asNeeded[x]: Take "as needed" (for x). One of these 2:
    "asNeededBoolean" : <boolean>,
    "asNeededCodeableConcept" : { CodeableConcept },
    // site[x]: Body site to administer to. One of these 2:
    "siteCodeableConcept" : { CodeableConcept },
    "siteReference" : { Reference(BodySite) },
    "route" : { CodeableConcept }, // How drug should enter body
    "method" : { CodeableConcept }, // Technique for administering medication
    // dose[x]: Amount of medication per dose. One of these 2:
    "doseRange" : { Range },
    "doseQuantity" : { Quantity(SimpleQuantity) },
    "maxDosePerPeriod" : { Ratio }, // Upper limit on medication per unit of time
    "maxDosePerAdministration" : { Quantity(SimpleQuantity) }, // Upper limit on medication per administration
    "maxDosePerLifetime" : { Quantity(SimpleQuantity) }, // Upper limit on medication per lifetime of the patient
    // rate[x]: Amount of medication per unit of time. One of these 3:
    "rateRatio" : { Ratio }
    "rateRange" : { Range }
    "rateQuantity" : { Quantity(SimpleQuantity) }
  }],
  "dispenseRequest" : { // Medication supply authorization
    "validityPeriod" : { Period }, // Time period supply is authorized for
    "numberOfRepeatsAllowed" : "<positiveInt>", // Number of refills authorized
    "quantity" : { Quantity(SimpleQuantity) }, // Amount of medication to supply per dispense
    "expectedSupplyDuration" : { Duration } // Number of days supply per dispense
  },
  "substitution" : { // Any restrictions on medication substitution
    "allowed" : <boolean>, // R!  Whether substitution is allowed or not
    "reason" : { CodeableConcept } // Why should (not) substitution be made
  },
  "priorPrescription" : { Reference(MedicationOrder) }, // An order/prescription that this supersedes
  "eventHistory" : [{ // A list of events of interest in the lifecycle
    "status" : "<code>", // R!  active | on-hold | completed | entered-in-error | stopped | draft
    "action" : { CodeableConcept }, // Action taken (e.g. verify, discontinue)
    "dateTime" : "<dateTime>", // R!  The date at which the event happened
    "actor" : { Reference(Practitioner) }, // Who took the action
    "reason" : { CodeableConcept } // Reason the action was taken
  }]
}

    partd =
    {
            "partDClaim": "Part D Claims",
            "claimType": "Part D",
            "claimNumber": "123456789012",
            "claimServiceDate": "20111117",
            "pharmacyServiceProvider": "123456789",
            "pharmacyName": "PHARMACY2 #00000",
            "drugCode": "00093013505",
            "drugName": "CARVEDILOL",
            "fillNumber": "0",
            "days'Supply": "30",
            "prescriberIdentifer": "123456789",
            "prescriberName": "Jane Doe",
            "category": "Part D Claims",
            "source": "MyMedicare.gov"
        }

     """

    rt = OrderedDict()
    rt['resourceType'] = "MedicationOrder"
    rt['meta'] = dt_meta()

    if 'claimNumber' in partd:
        rt['identifier'] = dt_identifier(partd['claimNumber'])

    if 'claimServiceDate' in partd:
        rt['dateWritten'] = date_yymmdd(partd['claimServiceDate'])

    if 'drugCode' in partd:
        drug = {"coding": [{"system": "https://www.accessdata.fda.gov/"
                                      "scripts/cder/ndc/",
                            "code": "51129288202"}]}
        if 'drugName' in partd:
            drug['text'] = partd['drugName']
        mcc = dt_codeable_concept(drug)
        if mcc:
            rt['medicationCodeableConcept'] = mcc

    if "days'Supply" in partd:
        dispense = {"expectedSupplyDuration": {"value": float(partd["days'Supply"]),
                                               "unit": "days"}}
        rt['dispenseRequest'] = dispense

    if 'fillNumber' in partd:
        rt['note'] = [{'text': "Fill number:%s" % partd['fillNumber']}]
    if patient:
        rt['patient'] = build_patient({'identifier': patient})
    careteam = []
    cm = {}
    if 'prescriberIdentifer' in partd:
        cm['providerIdentifier'] = dt_identifier(partd['prescriberIdentifer'])
        cm['role'] = dt_coding("Prescriber")
    if cm:
        careteam.append(cm)
    cm = {}
    if 'pharmacyServiceProvider' in partd:
        cm['providerIdentifier'] = dt_identifier(partd['pharmacyServiceProvider'])
        cm['role'] = dt_coding("Pharmacy")
    if cm:
        careteam.append(cm)

    item = {"sequence": "1",
            "careTeam": careteam}
    rt['item'] = [item]

    if rt:
        return rt
    else:
        return
