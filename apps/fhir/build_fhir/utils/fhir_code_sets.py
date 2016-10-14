#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
Project: hhs_oauth_server
App: apps.
FILE: fhir_code_sets
Created: 7/28/16 3:27 PM

Created by: ''
"""

true = True
false = False

# https://www.hl7.org/fhir/valueset-address-use.html
FHIR_ADDRESS_USE_CODE = ['home',
                         'work',
                         'temp',
                         'old']

# https://www.hl7.org/fhir/valueset-address-type.html
FHIR_ADDRESS_TYPE_CODE = ['postal',
                          'physical',
                          'both']

# http://hl7.org/fhir/ValueSet/contact-point-system
FHIR_CONTACTPOINT_SYSTEM_CODE = ['phone',
                                 'fax',
                                 'email',
                                 'pager',
                                 'other']

# https://www.hl7.org/fhir/valueset-contact-point-use.html
FHIR_CONTACTPOINT_USE_CODE = ['home',
                              'work',
                              'temp',
                              'old',
                              'mobile']

FHIR_HUMANNAME_USE_CODE = ['usual',
                           'official',
                           'temp',
                           'nickname',
                           'anonymous',
                           'old',
                           'maiden']

FHIR_IDENTIFIER_USE_CODE = ['usual',
                            'official',
                            'temp',
                            'secondary']

FHIR_LOCATION_STATUS_CODE = ['active',
                             'suspended',
                             'inactive']

FHIR_QUANTITY_COMP_CODE = ['<', '<=', '>=', '>']

# http://hl7.org/fhir/2016Sep/valueset-consent-category.html
FHIR_CONSENT_CODEABLE_CONCEPT = [({"code": "hipaa",
                                  "display": "HIPAA Authorization"}),
                                 ({"code": "nih-hipaa",
                                   "display": "HHS NIH HIPAA Research Authorization"}),
                                 ({"code": "nci",
                                   "display": "NCI Cancer Clinical Trial consent"}),
                                 ({"code": "nih-grdr",
                                   "display": "NIH Global Rare Disease Patient "
                                              "Registry and Data Repository consent"}),
                                 ({"code": "ga4gh",
                                   "display": "Population origins and ancestry "
                                              "research consent"})
                                 ]

# http://hl7.org/fhir/2016Sep/valueset-consent-status.html
FHIR_CONSENT_STATUS_CODE = ['draft',
                            'proposed',
                            'active',
                            'rejected',
                            'inactive',
                            'entered-in-error']

# http://hl7.org/fhir/2016Sep/valueset-consent-category.html
FHIR_CONSENT_CATEGORY_CODE = [
    {"code": "cat1",
     "display": "Advance Directive Consent examples",
     "property": [{"code": "notSelectable",
                   "valueBoolean": true}],
     "concept": [{"code": "advance-directive",
                  "display": "Advance Directive",
                  "definition": "Any instructions, written or given verbally by a patient "
                                "to a health care provider in anticipation of potential "
                                "need for medical treatment"}]},
    {"code": "cat2",
     "display": "Medical/Procedure Informed Consent",
     "definition": "RWJ funded toolkit has several international example consent "
                   "forms, and excellent overview of issues around medical informed consent",
     "property": [{"code": "notSelectable",
                   "valueBoolean": true}],
     "concept": [{"code": "medical-consent",
                  "display": "Medical Consent",
                  "definition": "Informed consent is the process of communication between "
                                "a patient and physician that results in the patient’s "
                                "authorization or agreement to undergo a specific medical "
                                "intervention [AMA 1998]. For both ethical and legal reasons, "
                                "patients must be given enough information to be fully informed "
                                "before deciding to undergo a major treatment, and this informed "
                                "consent must be documented in writing."}]},
    {"code": "cat3",
     "display": "Example of US jurisdictional [federal and state] privacy consent",
     "property": [{"code": "notSelectable",
                   "valueBoolean": true}],
     "concept": [{"code": "hipaa",
                  "display": "HIPAA Authorization",
                  "definition": "HIPAA 45 CFR Section 164.508 Uses and disclosures for "
                                "which an authorization is required. (a) Standard: "
                                "Authorizations for uses and disclosures. (1) Authorization "
                                "required: General rule. Except as otherwise permitted or "
                                "required by this subchapter, a covered entity may not use "
                                "or disclose protected health information without an authorization "
                                "that is valid under this section. When a covered entity obtains or "
                                "receives a valid authorization for its use or disclosure of "
                                "protected health information, such use or disclosure must be "
                                "consistent with such authorization. Usage Note: Authorizations "
                                "governed under this regulation meet the definition of an opt in "
                                "class of consent directive."},
                 {"code": "SSA-827",
                  "display": "SSA Authorization to Disclose",
                  "definition": "SA Form SSA-827 (Authorization to Disclose Information "
                                "to the Social Security Administration (SSA)). Form is "
                                "available at https://www.socialsecurity.gov/forms/ssa-827-inst-sp.pdf"}]},
    {"code": "cat4",
     "display": "US “Mixed” state HIE consent types",
     "definition": "May include federal and state jurisdictional privacy laws",
     "property": [{"code": "notSelectable",
                   "valueBoolean": true}],
     "concept": [{"code": "DCH-3927",
                  "display": "Michigan behavior and mental health consent",
                  "definition": "Michigan DCH-3927 Consent to Share Behavioral Health "
                                "Information for Care Coordination Purposes, which combines "
                                "42 CFR Part 2 and Michigan Mental Health Code, Act 258 of 1974. "
                                "Form is available at http://www.michigan.gov/documents/mdch/"
                                "DCH-3927_Consent_to_Share_Health_Information_477005_7.docx"},
                 {"code": "squaxin",
                  "display": "Squaxin Indian behavioral health and HIPAA consent",
                  "definition": "Squaxin Indian HIPAA and 42 CFR Part 2 Consent for Release "
                                "and Exchange of Confidential Information, which permits "
                                "consenter to select healthcare record type and types of "
                                "treatment purposes.  This consent requires disclosers and "
                                "recipients to comply with 42 C.F.R. Part 2, and HIPAA 45 C.F.R. "
                                "parts 160 and 164. It includes patient notice of the refrain "
                                "policy not to disclose without consent, and revocation rights. "
                                "https://www.ncsacw.samhsa.gov/files/SI_ConsentForReleaseAndExchange.PDF"}]},
    {"code": "cat5",
     "display": "Example international health information exchange consent type",
     "property": [{"code": "notSelectable", "valueBoolean": true}],
     "concept": [{"code": "nl-lsp",
                  "display": "NL LSP Permission",
                  "definition": "LSP (National Exchange Point) requires that providers, "
                                "hospitals and pharmacy obtain explicit permission [opt-in] "
                                "from healthcare consumers to submit and retrieve all or only "
                                "some of a subject of care’s health information collected by "
                                "the LSP for purpose of treatment, which can be revoked.  "
                                "Without permission, a provider cannot access LSP information "
                                "even in an emergency. The LSP provides healthcare consumers "
                                "with accountings of disclosures. https://www.vzvz.nl/uploaded/"
                                "FILES/htmlcontent/Formulieren/TOESTEMMINGSFORMULIER.pdf, "
                                "https://www.ikgeeftoestemming.nl/en, "
                                "https://www.ikgeeftoestemming.nl/en/registration/find-healthcare-provider"},
                 {"code": "at-elga",
                  "display": "AT ELGA Opt-in Consent",
                  "definition": "Pursuant to Sec. 2 no. 9 Health Telematics Act 2012, "
                                "ELGA Health Data ( “ELGA-Gesundheitsdaten”) = Medical documents. "
                                "Austria opted for an opt-out approach. This means that a person "
                                "is by default ‘ELGA participant’ unless he/she objects. "
                                "ELGA participants have the following options: General opt out: "
                                "No participation in ELGA, Partial opt-out: No participation in a "
                                "particular ELGA application, e.g. eMedication and Case-specific "
                                "opt-out: No participation in ELGA only regarding a particular "
                                "case/treatment. There is the possibility to opt-in again. "
                                "ELGA participants can also exclude the access of a particular "
                                "ELGA healthcare provider to a particular piece of or all of their "
                                "ELGA data. http://ec.europa.eu/health/ehealth/docs/laws_austria_en.pdf"}]},
    {"code": "cat6",
     "display": "Examples of US Research Consent Types",
     "property": [{"code": "notSelectable", "valueBoolean": true}],
     "concept": [{"code": "nih-hipaa",
                  "display": "HHS NIH HIPAA Research Authorization",
                  "definition": "Guidance and template form https://privacyruleandresearch.nih.gov"
                  "/pdf/authorization.pdf"},
                 {"code": "nci",
                  "display": "NCI Cancer Clinical Trial consent",
                  "definition": "see http://ctep.cancer.gov/protocolDevelopment/docs/"
                                "Informed_Consent_Template.docx"},
                 {"code": "nih-grdr",
                  "display": "NIH Global Rare Disease Patient Registry and Data Repository consent",
                  "definition": "Global Rare Disease Patient Registry and Data Repository ("
                                "GRDR) consent is an agreement of a healthcare consumer to permit "
                                "collection, access, use and disclosure of de-identified rare disease "
                                "information and collection of bio-specimens, medical information, "
                                "family history and other related information from patients to "
                                "permit the registry collection of health and genetic information, "
                                "and specimens for pseudonymized disclosure for research purpose "
                                "of use. https://rarediseases.info.nih.gov/files/informed_"
                                "consent_template.pdf"},
                 {"code": "va-10-10116",
                  "display": "VA Form 10-10116",
                  "definition": "VA Form 10-10116 Revocation of Authorization for Use and Release "
                                "of Individually Identifiable Health Information for Veterans Health "
                                "Administration Research. Note: VA Form 10-10116 is available "
                                "@ http://www.northerncalifornia.va.gov/northerncalifornia/services/"
                                "rnd/docs/vha-10-10116.pdf"},
                 {"code": "nih-527",
                  "display": "NIH Authorization for the Release of Medical Information",
                  "definition": "NIH Authorization for the Release of Medical Information is a "
                                "patient’s consent for the National Institutes of Health Clinical "
                                "Center to release medical information to care providers, which "
                                "can be revoked. Note: Consent Form available "
                                "@ http://cc.nih.gov/participate/_pdf/NIH-527.pdf"},
                 {"code": "ga4gh",
                  "display": "Population origins and ancestry research consent",
                  "definition": "Global Alliance for Genomic Health Data Sharing Consent Form "
                                "is an example of the GA4GH Population origins and ancestry "
                                "research consent form. Consenters agree to permitting a "
                                "specified research project to collect ancestry and genetic "
                                "information in controlled-access databases, and to allow other "
                                "researchers to use deidentified information from those databases. "
                                "http://www.commonaccord.org/index.php?action=doc&file=Wx/org/"
                                "genomicsandhealth/REWG/Demo/Roberta_Robinson_US"}]}
]
