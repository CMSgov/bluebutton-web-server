#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
hhs_oauth_server
FILE: progress
Created: 7/14/16 12:08 PM

File created by: ''
"""
import json

from collections import OrderedDict

# from django.template import loader
# from django.http import HttpResponse
# from django.shortcuts import RequestContext  # render

from apps.fhir.bluebutton.utils import (FhirServerUrl,
                                        request_call,
                                        get_crosswalk)


def get_fhir_claim(request, claim_number):
    """ Search for Claim Number in FHIR Backend

    Sample Search Specification:
     http://bluebuttonhapi-test.hhsdevcloud.us/baseDstu2/
     ExplanationOfBenefit
     ?identifier=CCW_PTA_FACT.CLM_ID|542612281109054

    Nothing found result:
     {"resourceType":"Bundle",
      "id":"62fe7fe3-9dca-4114-b753-6d7e874c34c5",
      "meta":{"lastUpdated":"2016-07-07T13:43:55.066+00:00"},
      "type":"searchset",
      "total":0,
      "link":[{"relation":"self",
               "url":"http://bluebuttonhapi-test.hhsdevcloud.us:80/baseDstu2/
               ExplanationOfBenefit
               ?identifier=CCW_PTA_FACT.CLM_ID%7C542612281109055"}]}

    Sample EOB Records
    {
            "fullUrl":"http://bluebuttonhapi-test.hhsdevcloud.us:80/baseDstu2/ExplanationOfBenefit/10",
            "resource":{
                "resourceType":"ExplanationOfBenefit",
                "id":"10",
                "extension":[
                    {
                        "url":"http://bluebutton.cms.hhs.gov/extensions#claimType",
                        "valueCoding":{
                            "system":"http://bluebutton.cms.hhs.gov/coding#claimType",
                            "code":"40",
                            "display":"Outpatient claim"
                        }
                    },
                    {
                        "url":"http://bluebutton.cms.hhs.gov/extensions#attendingPhysician",
                        "valueReference":{
                            "reference":"Practitioner/12"
                        }
                    },
                    {
                        "url":"http://bluebutton.cms.hhs.gov/extensions#operatingPhysician",
                        "valueReference":{
                            "reference":"Practitioner/13"
                        }
                    },
                    {
                        "url":"http://bluebutton.cms.hhs.gov/extensions#otherPhysician",
                        "valueReference":{
                            "reference":"Practitioner/14"
                        }
                    },
                    {
                        "url":"http://bluebutton.cms.hhs.gov/extensions#admittingDiagnosis",
                        "valueCoding":{
                            "system":"http://hl7.org/fhir/sid/icd-9-cm/diagnosis"
                        }
                    }
                ],
                "meta":{
                    "versionId":"1",
                    "lastUpdated":"2016-03-28T03:14:40.898+00:00"
                },
                "identifier":[
                    {
                        "system":"CCW_PTA_FACT.CLM_ID",
                        "value":"542612281109054"
                    }
                ],
                "billablePeriod":{
                    "start":"2008-11-15T00:00:00+00:00",
                    "end":"2008-11-15T00:00:00+00:00"
                },
                "provider":{
                    "reference":"Practitioner/11"
                },
                "diagnosis":[
                    {
                        "sequence":0,
                        "diagnosis":{
                            "system":"http://hl7.org/fhir/sid/icd-9-cm/diagnosis",
                            "code":"7137"
                        }
                    },
                    {
                        "sequence":1,
                        "diagnosis":{
                            "system":"http://hl7.org/fhir/sid/icd-9-cm/diagnosis",
                            "code":"72190"
                        }
                    }
                ],
                "patient":{
                    "reference":"Patient/1"
                },
                "coverage":{
                    "coverage":{
                        "reference":"Coverage/4"
                    }
                },
                "item":[
                    {
                        "type":{
                            "system":"http://hl7.org/fhir/ValueSet/v3-ActInvoiceGroupCode",
                            "code":"CSPINV"
                        },
                        "adjudication":[
                            {
                                "category":{
                                    "system":"CMS Adjudications",
                                    "code":"Line NCH Payment Amount"
                                },
                                "amount":{
                                    "value":10.00,
                                    "system":"urn:std:iso:4217",
                                    "code":"USD"
                                }
                            },
                            {
                                "category":{
                                    "system":"CMS Adjudications",
                                    "code":"NCH Primary Payer Claim Paid Amount"
                                },
                                "amount":{
                                    "value":0.00,
                                    "system":"urn:std:iso:4217",
                                    "code":"USD"
                                }
                            },
                            {
                                "category":{
                                    "system":"CMS Adjudications",
                                    "code":"NCH Beneficiary Blood Deductible Liability Amount"
                                },
                                "amount":{
                                    "value":0.00,
                                    "system":"urn:std:iso:4217",
                                    "code":"USD"
                                }
                            },
                            {
                                "category":{
                                    "system":"CMS Adjudications",
                                    "code":"NCH Beneficiary Part B Deductible Amount"
                                },
                                "amount":{
                                    "value":0.00,
                                    "system":"urn:std:iso:4217",
                                    "code":"USD"
                                }
                            },
                            {
                                "category":{
                                    "system":"CMS Adjudications",
                                    "code":"NCH Beneficiary Part B Coinsurance Amount"
                                },
                                "amount":{
                                    "value":0.00,
                                    "system":"urn:std:iso:4217",
                                    "code":"USD"
                                }
                            }
                        ],
                        "detail":[
                            {
                                "extension":[
                                    {
                                        "url":"http://bluebutton.cms.hhs.gov/extensions#diagnosisLinkId",
                                        "valueInteger":0
                                    },
                                    {
                                        "url":"http://bluebutton.cms.hhs.gov/extensions#diagnosisLinkId",
                                        "valueInteger":1
                                    }
                                ],
                                "sequence":1,
                                "type":{
                                    "system":"http://hl7.org/fhir/ValueSet/v3-ActInvoiceGroupCode",
                                    "code":"CSPINV"
                                },
                                "service":{
                                    "system":"HCPCS",
                                    "code":"73564"
                                }
                            }
                        ]
                    }
                ]
            },
            "search":{
                "mode":"match"
            }
        },
        {
            "fullUrl":"http://bluebuttonhapi-test.hhsdevcloud.us:80/baseDstu2/ExplanationOfBenefit/15",
            "resource":{
                "resourceType":"ExplanationOfBenefit",
                "id":"15",
                "extension":[
                    {
                        "url":"http://bluebutton.cms.hhs.gov/extensions#claimType",
                        "valueCoding":{
                            "system":"http://bluebutton.cms.hhs.gov/coding#claimType",
                            "code":"40",
                            "display":"Outpatient claim"
                        }
                    },
                    {
                        "url":"http://bluebutton.cms.hhs.gov/extensions#attendingPhysician",
                        "valueReference":{
                            "reference":"Practitioner/17"
                        }
                    },
                    {
                        "url":"http://bluebutton.cms.hhs.gov/extensions#operatingPhysician",
                        "valueReference":{
                            "reference":"Practitioner/18"
                        }
                    },
                    {
                        "url":"http://bluebutton.cms.hhs.gov/extensions#otherPhysician",
                        "valueReference":{
                            "reference":"Practitioner/19"
                        }
                    },
                    {
                        "url":"http://bluebutton.cms.hhs.gov/extensions#admittingDiagnosis",
                        "valueCoding":{
                            "system":"http://hl7.org/fhir/sid/icd-9-cm/diagnosis"
                        }
                    }
                ],
                "meta":{
                    "versionId":"1",
                    "lastUpdated":"2016-03-28T03:14:40.898+00:00"
                },
                "identifier":[
                    {
                        "system":"CCW_PTA_FACT.CLM_ID",
                        "value":"542062281310767"
                    }
                ],
                "billablePeriod":{
                    "start":"2009-02-02T00:00:00+00:00",
                    "end":"2009-02-02T00:00:00+00:00"
                },
                "provider":{
                    "reference":"Practitioner/16"
                },
                "diagnosis":[
                    {
                        "sequence":0,
                        "diagnosis":{
                            "system":"http://hl7.org/fhir/sid/icd-9-cm/diagnosis",
                            "code":"49321"
                        }
                    }
                ],
                "patient":{
                    "reference":"Patient/1"
                },
                "coverage":{
                    "coverage":{
                        "reference":"Coverage/4"
                    }
                },
                "item":[
                    {
                        "type":{
                            "system":"http://hl7.org/fhir/ValueSet/v3-ActInvoiceGroupCode",
                            "code":"CSPINV"
                        },
                        "adjudication":[
                            {
                                "category":{
                                    "system":"CMS Adjudications",
                                    "code":"Line NCH Payment Amount"
                                },
                                "amount":{
                                    "value":900.00,
                                    "system":"urn:std:iso:4217",
                                    "code":"USD"
                                }
                            },
                            {
                                "category":{
                                    "system":"CMS Adjudications",
                                    "code":"NCH Primary Payer Claim Paid Amount"
                                },
                                "amount":{
                                    "value":0.00,
                                    "system":"urn:std:iso:4217",
                                    "code":"USD"
                                }
                            },
                            {
                                "category":{
                                    "system":"CMS Adjudications",
                                    "code":"NCH Beneficiary Blood Deductible Liability Amount"
                                },
                                "amount":{
                                    "value":0.00,
                                    "system":"urn:std:iso:4217",
                                    "code":"USD"
                                }
                            },
                            {
                                "category":{
                                    "system":"CMS Adjudications",
                                    "code":"NCH Beneficiary Part B Deductible Amount"
                                },
                                "amount":{
                                    "value":0.00,
                                    "system":"urn:std:iso:4217",
                                    "code":"USD"
                                }
                            },
                            {
                                "category":{
                                    "system":"CMS Adjudications",
                                    "code":"NCH Beneficiary Part B Coinsurance Amount"
                                },
                                "amount":{
                                    "value":20.00,
                                    "system":"urn:std:iso:4217",
                                    "code":"USD"
                                }
                            }
                        ],
                        "detail":[
                            {
                                "extension":[
                                    {
                                        "url":"http://bluebutton.cms.hhs.gov/extensions#diagnosisLinkId",
                                        "valueInteger":0
                                    }
                                ],
                                "sequence":1,
                                "type":{
                                    "system":"http://hl7.org/fhir/ValueSet/v3-ActInvoiceGroupCode",
                                    "code":"CSPINV"
                                },
                                "service":{
                                    "system":"HCPCS",
                                    "code":"99214"
                                }
                            }
                        ]
                    }
                ]
            },
            "search":{
                "mode":"match"
            }
        },


    """

    # We need the crosswalk to check client auth for the server
    cx = get_crosswalk(request.user)
    # Get the FHIR Server URL
    # Construct the Search for ExplanationOfBenefit / PatientClaimSummary
    search_base = FhirServerUrl() + "ExplanationOfBenefit"

    # FHIR_URL + PATH + RELEASE + ExplanationOfBenefit?
    # claimIdentifier=claim_number
    # &_format=json

    # http://bluebuttonhapi-test.hhsdevcloud.us/baseDstu2/
    # ExplanationOfBenefit?identifier=CCW_PTA_FACT.CLM_ID|542882280967266

    search_base += "?_format=json&identifier="  # CCW_PTA_FACT.CLM_ID|"

    fhir_claim = {}
    fhir_claim['claimNumber'] = claim_number
    fhir_claim['found'] = False

    search_base += claim_number

    # logger.debug('Calling request_call with %s' % search_base)
    r = request_call(request, search_base, cx)
    # logger.debug("returned with %s" % r.text)
    bundle = json.loads(r.text, object_pairs_hook=OrderedDict)
    resource = {}
    if bundle['total'] > 0:
        resource = bundle['entry'][0]['resource']
    # If claim is found:
        fhir_claim['found'] = True
        fhir_claim['claimIdentifier'] = resource['identifier'][0]['value']
        fhir_claim['identifier'] = resource['id']
        fhir_claim['provider'] = resource['provider']['reference']
        fhir_claim['patient'] = resource['patient']['reference']
        if 'billablePeriod' in resource:
            if isinstance(resource['billablePeriod'], dict):
                fhir_claim['timingPeriod'] = dict(resource['billablePeriod'])
            else:
                fhir_claim['timingPeriod'] = resource['billablePeriod']
    # fhir_claim['claimIdentifier'] = ExplanationOfBenefit.claimIdentifier
    # fhir_claim['identifier'] = ExplanationOfBenefit.identifier
    # fhir_claim['provider'] = ExplanationOfBenefit.providerIdentifier
    # fhir_claim['patient'] = ExplanationOfBenefit.patientIdentifier
    # fhir_claim['timingPeriod'] = ExplanationOfBenefit.timingPeriod
    print("\nSearch for claim:", claim_number)
    print("\Resources:", resource)
    print("\nFound:", fhir_claim)
    # logger.debug('fhir_claim: %s' % fhir_claim)

    return fhir_claim


def check_patient(fhir_patient, patient):
    """ Compare Patient Info """

    # Get the FHIR Patient Resources
    # Compare to patient information from blue button file

    matched = False
    # if match:
    #     matched = True

    return matched
