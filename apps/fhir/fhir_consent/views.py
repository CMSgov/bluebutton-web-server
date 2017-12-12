import logging
from django.conf import settings

from ..bluebutton.utils import (dt_patient_reference)
from ..build_fhir.utils.utils import get_guid
from ..build_fhir.utils.utils_fhir_dt import (dt_identifier,
                                              dt_code,
                                              dt_coding,
                                              dt_codeable_concept,
                                              dt_instant,
                                              dt_narrative,
                                              rt_device,
                                              rt_initialize,
                                              dt_system_attachment,
                                              rt_cms_organization)
from ..build_fhir.utils.fhir_code_sets import (FHIR_CONSENT_CODEABLE_CONCEPT,
                                               FHIR_CONSENT_STATUS_CODE)
from .utils import resource_from_scopes

BB_CONSENT_AGREEMENT_URL = settings.BB_CONSENT['AGREEMENT_URL']
BB_CONSENT_URL_TITLE = settings.BB_CONSENT['URL_TITLE']
BB_CONSENT_POLICY_URL = settings.BB_CONSENT['POLICY_URL']

logger = logging.getLogger('hhs_server.%s' % __name__)

# STU3 Consent: http://hl7.org/fhir/2016Sep/consent.html
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


def default_consent_directive():
    """ Setup default DSTU2 Contract Json ConsentDirective  """

    rt = rt_consent_activate()

    return rt


def default_consent():
    """
    setup default STU3 fhir json consent_directive
    :return:
    """
    rt = rt_consent_activate()
    # rt['status'] = dt_consent_status('draft')

    return rt


def rt_consent_directive_activate(user,
                                  appname,
                                  narrative,
                                  oauth_period,
                                  oauth_permission):
    """ create JSON ConsentDirective """

    rt = rt_initialize("ConsentDirective")
    rt['identifier'] = dt_identifier(get_guid())
    rt['text'] = dt_narrative(narrative)
    rt['issued'] = dt_instant()

    # oauth_period is formated using dt_period
    rt['applies'] = oauth_period

    # List of resources extracted from scopes
    resource_list = resource_from_scopes(oauth_permission)
    if resource_list:
        rt['subject'] = resource_list

    rt['authority'] = rt_cms_organization("minimal")
    rt['type'] = dt_coding({"code": "privacy"})
    # TODO: If Sync4Science scopes then include NIH Privacy type
    rt['subType'] = dt_consent_category("hipaa")

    rt['actor'] = [{'entity': dt_patient_reference(user),
                    'role': dt_codeable_concept('beneficiary')},
                   {'entity': rt_device(appname),
                    'role': dt_codeable_concept('application')}]

    rt['signer'] = [{'type': dt_coding({"display": "Consent"}),
                     'party': dt_patient_reference(user)}]

    rt['bindingAttachment'] = dt_system_attachment(BB_CONSENT_AGREEMENT_URL,
                                                   BB_CONSENT_URL_TITLE)

    return rt


def rt_consent_activate(user, app, oauth_period, oauth_permission):
    """ create JSON Resource for Consent """

    rt = rt_initialize("Consent")
    rt['identifier'] = dt_identifier(get_guid())

    status = dt_consent_status('active')
    if status:
        rt['status'] = status

    category = dt_consent_category()
    if category:
        rt['category'] = category
    rt['dateTime'] = dt_instant()

    # oauth_period is formated using dt_period
    rt['period'] = oauth_period
    rt['patient'] = dt_patient_reference(user)

    # Consentor will be the Patient that is connecting an app to their data.
    rt['consentor'] = rt['patient']

    # CMS Manages the Consent
    rt['organization'] = rt_cms_organization("minimal")
    rt['sourceAttachment'] = dt_system_attachment(BB_CONSENT_AGREEMENT_URL,
                                                  BB_CONSENT_URL_TITLE)
    rt['policy'] = BB_CONSENT_POLICY_URL
    rt['recipient'] = rt_device(app)

    # oauth_permission dict (scopes)
    rt['pupose'] = oauth_permission

    return rt


def dt_consent_status(status="draft"):
    """ Set Status - Default = "draft" """

    return dt_code(status.lower, FHIR_CONSENT_STATUS_CODE)


def dt_consent_category(consent_type="hipaa"):
    """ Select Consent Codeable Concept """

    if consent_type:
        for item in FHIR_CONSENT_CODEABLE_CONCEPT:
            if 'code' in item:
                # logger.debug("\nITEM: %s" % item['code'])
                if item['code'] == consent_type:
                    return dt_codeable_concept(item)

    return None
