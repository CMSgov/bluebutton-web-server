#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
# flake8: noqa
"""
hhs_oauth_server
FILE: sample_json_bb_claim
Created: 8/5/16 12:11 PM

File created by: ''
"""

SAMPLE_BB_CLAIM_PART_A = """
{
            "claim": "claim Header",
            "claimNumber": "12345678900000VAA",
            "provider": "No Information Available",
            "providerBillingAddress": "",
            "date": {
                "serviceStartDate": "20120922",
                "serviceEndDate": ""
            },
            "charges": {
                "amountCharged": "$504.80",
                "medicareApproved": "$504.80",
                "providerPaid": "$126.31",
                "youMayBeBilled": "$38.84"
            },
            "claimType": "Outpatient",
            "diagnosisCode1": "56400",
            "diagnosisCode2": "7245",
            "diagnosisCode3": "V1588",
            "category": "claim Header",
            "source": "MyMedicare.gov",
            "details": [
                {
                    "details": "Claim Lines for Claim Number",
                    "lineNumber": "1",
                    "dateOfServiceFrom": "20120922",
                    "revenueCodeDescription": "0250 - General Classification PHARMACY",
                    "procedureCodeDescription": "",
                    "modifier1Description": "",
                    "modifier2Description": "",
                    "modifier3Description": "",
                    "modifier4Description": "",
                    "quantityBilledUnits": "1",
                    "submittedAmountCharges": "$14.30",
                    "allowedAmount": "$14.30",
                    "nonCovered": "$0.00",
                    "category": "Claim Lines for Claim Number",
                    "source": "MyMedicare.gov",
                    "claimNumber": "12345678900000VAA"
                },
                {
                    "lineNumber": "2",
                    "dateOfServiceFrom": "20120922",
                    "revenueCodeDescription": "0320 - General Classification DX X-RAY",
                    "procedureCodeDescription": "74020 - Radiologic Examination, Abdomen; Complete, Including Decubitus And/Or Erect Views",
                    "modifier1Description": "",
                    "modifier2Description": "",
                    "modifier3Description": "",
                    "modifier4Description": "",
                    "quantityBilledUnits": "1",
                    "submittedAmountCharges": "$175.50",
                    "allowedAmount": "$175.50",
                    "nonCovered": "$0.00",
                    "category": "Claim Lines for Claim Number",
                    "source": "MyMedicare.gov",
                    "claimNumber": "12345678900000VAA"
                },
                {
                    "lineNumber": "3",
                    "dateOfServiceFrom": "20120922",
                    "revenueCodeDescription": "0450 - General Classification EMERG ROOM",
                    "procedureCodeDescription": "99283 - Emergency Department Visit For The Evaluation And Management Of A Patient, Which Requires Th",
                    "modifier1Description": "25 - Significant, Separately Identifiable Evaluation And Management Service By The Same Physician On",
                    "modifier2Description": "",
                    "modifier3Description": "",
                    "modifier4Description": "",
                    "quantityBilledUnits": "1",
                    "submittedAmountCharges": "$315.00",
                    "allowedAmount": "$315.00",
                    "nonCovered": "$0.00",
                    "category": "Claim Lines for Claim Number",
                    "source": "MyMedicare.gov",
                    "claimNumber": "12345678900000VAA"
                },
                {
                    "lineNumber": "4",
                    "dateOfServiceFrom": "",
                    "revenueCodeDescription": "0001 - Total Charges",
                    "procedureCodeDescription": "",
                    "modifier1Description": "",
                    "modifier2Description": "",
                    "modifier3Description": "",
                    "modifier4Description": "",
                    "quantityBilledUnits": "0",
                    "submittedAmountCharges": "$504.80",
                    "allowedAmount": "$504.80",
                    "nonCovered": "$0.00",
                    "category": "Claim Lines for Claim Number",
                    "source": "MyMedicare.gov",
                    "claimNumber": "12345678900000VAA"
                }
            ]
        }
"""

SAMPLE_BB_CLAIM_PART_B = """
{
            "claims": "Claim Summary",
            "claimNumber": "1234567890000",
            "provider": "No Information Available",
            "providerBillingAddress": "",
            "date": {
                "serviceStartDate": "20121018",
                "serviceEndDate": ""
            },
            "charges": {
                "amountCharged": "$60.00",
                "medicareApproved": "$34.00",
                "providerPaid": "$27.20",
                "youMayBeBilled": "$6.80"
            },
            "claimType": "PartB",
            "diagnosisCode1": "3534",
            "diagnosisCode2": "7393",
            "diagnosisCode3": "7392",
            "diagnosisCode4": "3533",
            "category": "Claim Summary",
            "source": "MyMedicare.gov",
            "details": [
                {
                    "details": "Claim Lines for Claim Number",
                    "lineNumber": "1",
                    "dateOfServiceFrom": "20121018",
                    "dateOfServiceTo": "20121018",
                    "procedureCodeDescription": "98941 - Chiropractic Manipulative Treatment (Cmt); Spinal, Three To Four Regions",
                    "modifier1Description": "AT - Acute Treatment (This Modifier Should Be Used When Reporting Service 98940, 98941, 98942)",
                    "modifier2Description": "",
                    "modifier3Description": "",
                    "modifier4Description": "",
                    "quantityBilledUnits": "1",
                    "submittedAmountCharges": "$60.00",
                    "allowedAmount": "$34.00",
                    "nonCovered": "$26.00",
                    "placeOfServiceDescription": "11 - Office",
                    "typeOfServiceDescription": "1 - Medical Care",
                    "renderingProviderNo": "0000001",
                    "renderingProviderNpi": "123456789",
                    "category": "Claim Lines for Claim Number",
                    "source": "MyMedicare.gov",
                    "claimNumber": "1234567890000"
                }
            ]
        }
"""

SAMPLE_BB_CLAIM_PART_D = """
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
