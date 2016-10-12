import logging
# from django.shortcuts import render
# from collections import OrderedDict

from ..build_fhir.utils.utils import (get_guid, pretty_json)
from ..build_fhir.utils.utils_fhir_dt import (dt_identifier,
                                              dt_codeable_concept,
                                              rt_initialize)
from ..build_fhir.utils.fhir_code_sets import FHIR_CONSENT_CODEABLE_CONCEPT

logger = logging.getLogger('hhs_server.%s' % __name__)


json_consent_stu3 = """
{
  "resourceType" : "Consent",
  "identifier" : { %s },
  "status" : "<code>", // R!  draft | proposed | active | rejected | inactive | entered-in-error
  "category" : [{ CodeableConcept }], // Classification of the consent statement - for indexing/retrieval
  "dateTime" : "<dateTime>", // When this Consent was created or indexed
  "period" : { Period }, // Period that this consent applies
  "patient" : { Reference(Patient) }, // R!  Who the consent applies to
  "consentor" : [{ Reference(Organization|Patient|Practitioner|RelatedPerson) }], // Who is agreeing to the policy and exceptions
  "organization" : { Reference(Organization) }, // Organization that manages the consent
  // source[x]: Source from which this consent is taken. One of these 3:
  "sourceAttachment" : { Attachment },
  "sourceIdentifier" : { Identifier },
  "sourceReference" : { Reference(Consent|DocumentReference|Contract|
   QuestionnaireResponse) },
  "policy" : "<uri>", // R!  Policy that this consents to
  "recipient" : [{ Reference(Device|Group|Organization|Patient|Practitioner|
   RelatedPerson|CareTeam) }], // Whose access is controlled by the policy
  "purpose" : [{ Coding }], // Context of activities for which the agreement is made
  "except" : [{ // Additional rule -  addition or removal of permissions
    "type" : "<code>", // R!  deny | permit
    "period" : { Period }, // Timeframe for data controlled by this exception
    "actor" : [{ // Who|what controlled by this exception (or group, by role)
      "role" : { CodeableConcept }, // R!  How the actor is/was involved
      "reference" : { Reference(Device|Group|CareTeam|Organization|Patient|
     Practitioner|RelatedPerson) } // R!  Resource for the actor (or group, by role)
    }],
    "action" : [{ CodeableConcept }], // Actions controlled by this exception
    "securityLabel" : [{ Coding }], // Security Labels that define affected resources
    "purpose" : [{ Coding }], // Context of activities covered by this exception
    "class" : [{ Coding }], // e.g. Resource Type, Profile, or CDA etc
    "code" : [{ Coding }], // e.g. LOINC or SNOMED CT code, etc in the content
    "data" : [{ // Data controlled by this exception
      "meaning" : "<code>", // R!  instance | related | dependents
      "reference" : { Reference(Any) } // R!  The actual data reference
    }]
  }]
}
    """


def default_consent():
    """
    setup default fhir json consent_directive
    :return:
    """
    rt = rt_consent_initialize()
    rt.status = dt_consent_status('draft')


def rt_consent_initialize():
    """ create JSON Resource for Consent """

    rt = rt_initialize("Consent")
    rt['identifier'] = dt_identifier(get_guid())
    status = dt_consent_status('active')
    if status:
        rt['status'] = status
    category = dt_consent_category()
    if category:
        rt['category'] = category

    print("\n%s" % pretty_json(rt))
    return rt


def dt_consent_status(mode="draft"):
    """ Set Status - Default = "draft" """

    status_choice = ['draft',
                     'proposed',
                     'active',
                     'rejected',
                     'inactive',
                     'entered-in-error']

    if mode in status_choice:
        status = mode
        return status
    else:
        return


def dt_consent_category(consent_type="hipaa"):
    """ Select Consent Codeable Concept """

    if consent_type:
        for item in FHIR_CONSENT_CODEABLE_CONCEPT:
            if 'code' in item:
                logger.debug("\nITEM: %s" % item['code'])
                if item['code'] == consent_type:
                    return dt_codeable_concept(item)

    return None
