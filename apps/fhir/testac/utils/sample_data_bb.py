#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4
# flake8: noqa
"""
hhs_oauth_server
apps.fhir.testac.utils
FILE: sample_data_bb
Created: 7/25/16 5:05 PM

File created by: Mark Scrimshire @ekivemark
"""

SAMPLE_BB_TEXT = """
--------------------------------
MYMEDICARE.GOV PERSONAL HEALTH INFORMATION

--------------------------------
**********CONFIDENTIAL***********

Produced by the Blue Button (v2.0)

03/16/2013 5:10 AM




--------------------------------
Demographic

--------------------------------

Source: MyMedicare.gov



Name: JOHN DOE

Date of Birth: 01/01/1910

Address Line 1: 123 ANY ROAD

Address Line 2:

City: ANYTOWN

State: VA

Zip: 00001

Phone Number: 123-456-7890

Email: JOHNDOE@example.com

Part A Effective Date: 01/01/2012

Part B Effective Date: 01/01/2012



--------------------------------
Emergency Contact

--------------------------------

Source: Self-Entered



Contact Name: JANE DOE

Address Type:Home

Address Line 1: 123 AnyWhere St

Address Line 2:

City: AnyWhere

State: DC

Zip: 00002-1111

Relationship: Other

Home Phone: 123-456-7890

Work Phone: 000-001-0001

Mobile Phone: 000-001-0002

Email Address: JANEDOE@example.com



Contact Name: STEVE DOE

Address Type:

Address Line 1: 123 AnyWhere Rd

Address Line 2:

City: AnyWhere

State: VA

Zip: 00001

Relationship: Other

Home Phone: 123-456-7890

Work Phone: 000-001-0001

Mobile Phone: 000-001-0002

Email Address: STEVEDOE@example.com



--------------------------------
Self Reported Medical Conditions

--------------------------------

Source: Self-Entered



Condition Name: Arthritis

Medical Condition Start Date: 08/09/2005

Medical Condition End Date: 02/28/2011



Condition Name: Asthma

Medical Condition Start Date: 01/25/2008

Medical Condition End Date: 01/25/2010



--------------------------------
Self Reported Allergies

--------------------------------

Source: Self-Entered



Allergy Name: Antibotic

Type: Drugs

Reaction: Vomiting

Severity: Severe

Diagnosed: Yes

Treatment: Allergy Shots

First Episode Date: 01/08/1926

Last Episode Date: 03/13/1955

Last Treatment Date: 09/28/1949

Comments: Erythromycin



Allergy Name: Grasses

Type: Environmental

Reaction: Sneezing

Severity: Severe

Diagnosed: Yes

Treatment: Avoidance

First Episode Date: 05/13/1973

Last Episode Date: 07/20/1996

Last Treatment Date: 09/27/2008

Comments:



--------------------------------
Self Reported Implantable Device

--------------------------------

Source: Self-Entered



Device Name: Artificial Eye Lenses

Date Implanted: 1/27/1942



--------------------------------
Self Reported Immunizations

--------------------------------

Source: Self-Entered



Immunization Name: Varicella/Chicken Pox

Date Administered:04/21/2002

Method: Nasal Spray(mist)

Were you vaccinated in the US:

Comments: congestion

Booster 1 Date: 02/02/1990

Booster 2 Date:

Booster 3 Date:



Immunization Name: typhoid

Date Administered:01/02/2009

Method: Injection

Were you vaccinated in the US:

Comments:

Booster 1 Date:

Booster 2 Date:

Booster 3 Date:



--------------------------------
Self Reported Labs and Tests

--------------------------------

Source: Self-Entered



Test/Lab Type: Glucose Level
Date Taken: 03/21/2008

Administered by: AnyLab

Requesting Doctor: Dr. Smith

Reason Test/Lab Requested: Ongoing elevated glucose

Results: 135, 170, 150, 120

Comments: Fasting, hour 1, hour 2, hour 3



--------------------------------
Self Reported Vital Statistics

--------------------------------

Source: Self-Entered



Vital Statistic Type: Blood Pressure

Date: 07/22/2011

Time: 3:00 PM

Reading: 120/80

Comments:



Vital Statistic Type: Glucose

Date: 03/20/2012

Time: 12:00 PM

Reading: 110

Comments:



--------------------------------
Family Medical History

--------------------------------

Source: Self-Entered



Family Member: Brother

Type:

DOB:1/10/1915

DOD:

Age:

Type: Allergy

Description: Antiarrythmia

Description: Antibiotic

Description: Anticonvulsants

Type: Condition

Description: Allergies

Description: Alzheimer's Disease

Description: Angina (Heart Pain)

Description: Cataracts


--------------------------------
Drugs

--------------------------------

Source: Self-Entered



Drug Name: Aspirin

Supply: Dialy

Orig Drug Entry: Aspirin



--------------------------------
Preventive Services

--------------------------------

Source: MyMedicare.gov



Description: DIABETES

Next Eligible Date: 10/1/2011

Last Date of Service:



Description: PAP TEST DR

Next Eligible Date: 10/1/2011

Last Date of Service:



Description: ABDOMINAL AORTIC ANEURYSM

Next Eligible Date: 7/1/2012

Last Date of Service:



Description: ANNUAL WELLNESS VISIT

Next Eligible Date: 1/1/2013

Last Date of Service:



Description: DEPRESSION SCREENING

Next Eligible Date: 10/14/2012

Last Date of Service:



--------------------------------
Providers

--------------------------------

Source: Self-Entered



Provider Name: ANY CARE

Provider Address: 123 Any Rd, Anywhere, MD 99999

Type: NHC

Specialty:

Medicare Provider: Not Available



Provider Name: ANY HOSPITAL1

Provider Address: 123 Drive, Anywhere, VA 00001

Type: HOS

Specialty:

Medicare Provider: Not Available

Provider Name: Jane Doe

Provider Address: 123 Road, Anywhere, VA 00001

Type: PHY

Specialty: Other

Medicare Provider: Not Available



--------------------------------
Pharmacies

--------------------------------

Source: Self-Entered



Pharmacy Name: PHARMACY, EAST STREET ANYWHERE, DC 00002

Pharmacy Phone: 000-000-0001



Pharmacy Name: ANY PHARMACY, WEST STREET ANYWHERE, VA 00001

Pharmacy Phone: 000-000-0002



--------------------------------
Plans

--------------------------------

Source: MyMedicare.gov



Contract ID/Plan ID: H9999/9999

Plan Period: 09/01/2011 - current

Plan Name: A Medicare Plan Plus (HMO)

Marketing Name: HealthCare Payer

Plan Address: 123 Any Road Anytown PA 00003

Plan Type: 3 - Coordinated Care Plan (HMO, PPO, PSO, SNP)



Contract ID/Plan ID: S9999/000

Plan Period: 01/01/2010 - current

Plan Name: A Medicare Rx Plan (PDP)

Marketing Name: Another HealthCare Payer

Plan Address: 123 Any Road Anytown PA 00003

Plan Type: 11 - Medicare Prescription Drug Plan



--------------------------------
Employer Subsidy

--------------------------------

Source: MyMedicare.gov


Employer Plan: STATE HEALTH BENEFITS PROGRAM

Employer Subsidy Start Date: 01/01/2011

Employer Subsidy End Date: 12/31/2011


--------------------------------
Primary Insurance

--------------------------------

Source: MyMedicare.gov



MSP Type: End stage Renal Disease (ESRD)

Policy Number: 1234567890

Insurer Name: Insurer1

Insurer Address: PO BOX 0000 Anytown, CO 00002-0000

Effective Date: 01/01/2011

Termination Date: 09/30/2011



MSP Type: End stage Renal Disease (ESRD)

Policy Number: 12345678901

Insurer Name: Insurer2

Insurer Address: 0000 Any ROAD ANYWHERE, VA 00000-0000

Effective Date: 01/01/2010

Termination Date: 12/31/2010



--------------------------------
Other Insurance

--------------------------------

Source: MyMedicare.gov



MSP Type:

Policy Number: 00001

Insurer Name: Insurer

Insurer Address: 00 Address STREET ANYWHERE, PA 00000

Effective Date: 10/01/1984

Termination Date: 11/30/2008



--------------------------------
Claim Summary

--------------------------------

Source: MyMedicare.gov



Claim Number: 1234567890000

Provider: No Information Available
Provider Billing Address:

Service Start Date: 10/18/2012

Service End Date:

Amount Charged: $60.00

Medicare Approved: $34.00

Provider Paid: $27.20

You May be Billed: $6.80

Claim Type: PartB

Diagnosis Code 1: 3534
Diagnosis Code 2: 7393
Diagnosis Code 3: 7392
Diagnosis Code 4: 3533

--------------------------------
Claim Lines for Claim Number: 1234567890000

--------------------------------



Line number:  1

Date of Service From:  10/18/2012

Date of Service To:  10/18/2012

Procedure Code/Description:  98941 - Chiropractic Manipulative Treatment (Cmt); Spinal, Three To Four Regions

Modifier 1/Description:  AT - Acute Treatment (This Modifier Should Be Used When Reporting Service 98940, 98941, 98942)

Modifier 2/Description:

Modifier 3/Description:

Modifier 4/Description:

Quantity Billed/Units:  1

Submitted Amount/Charges:  $60.00

Allowed Amount:  $34.00

Non-Covered:  $26.00

Place of Service/Description:  11 - Office

Type of Service/Description:  1 - Medical Care

Rendering Provider No:  0000001

Rendering Provider NPI:  123456789



--------------------------------



--------------------------------



Claim Number: 12345678900000VAA

Provider: No Information Available

Provider Billing Address:

Service Start Date: 09/22/2012

Service End Date:

Amount Charged: $504.80

Medicare Approved: $504.80

Provider Paid: $126.31

You May be Billed: $38.84

Claim Type: Outpatient

Diagnosis Code 1: 56400
Diagnosis Code 2: 7245
Diagnosis Code 3: V1588

--------------------------------
Claim Lines for Claim Number: 12345678900000VAA

--------------------------------



Line number:  1

Date of Service From:  09/22/2012

Revenue Code/Description: 0250 - General Classification PHARMACY

Procedure Code/Description:

Modifier 1/Description:

Modifier 2/Description:

Modifier 3/Description:

Modifier 4/Description:

Quantity Billed/Units:  1

Submitted Amount/Charges:  $14.30

Allowed Amount:  $14.30

Non-Covered:  $0.00



Line number:  2

Date of Service From:  09/22/2012

Revenue Code/Description: 0320 - General Classification DX X-RAY

Procedure Code/Description:  74020 - Radiologic Examination, Abdomen; Complete, Including Decubitus And/Or Erect Views

Modifier 1/Description:

Modifier 2/Description:

Modifier 3/Description:

Modifier 4/Description:

Quantity Billed/Units:  1

Submitted Amount/Charges:  $175.50

Allowed Amount:  $175.50

Non-Covered:  $0.00



Line number:  3

Date of Service From:  09/22/2012

Revenue Code/Description: 0450 - General Classification EMERG ROOM

Procedure Code/Description:  99283 - Emergency Department Visit For The Evaluation And Management Of A Patient, Which Requires Th

Modifier 1/Description:  25 - Significant, Separately Identifiable Evaluation And Management Service By The Same Physician On

Modifier 2/Description:

Modifier 3/Description:

Modifier 4/Description:

Quantity Billed/Units:  1

Submitted Amount/Charges:  $315.00

Allowed Amount:  $315.00

Non-Covered:  $0.00



Line number:  4

Date of Service From:

Revenue Code/Description: 0001 - Total Charges

Procedure Code/Description:

Modifier 1/Description:

Modifier 2/Description:

Modifier 3/Description:

Modifier 4/Description:

Quantity Billed/Units:  0

Submitted Amount/Charges:  $504.80

Allowed Amount:  $504.80

Non-Covered:  $0.00

Claim Number: 1234567890123

Provider: No Information Available

Provider Billing Address:

Service Start Date: 12/01/2012

Service End Date:

Amount Charged: * Not Available *

Medicare Approved: * Not Available *

Provider Paid: * Not Available *

You May be Billed: * Not Available *

Claim Type: PartB

Diagnosis Code 1: 7392
Diagnosis Code 2: 7241
Diagnosis Code 3: 7393
Diagnosis Code 4: 7391

--------------------------------
Claim Lines for Claim Number: 1234567890123

--------------------------------



Line number:  1

Date of Service From:  12/01/2012

Date of Service To:  12/01/2012

Procedure Code/Description:  98941 - Chiropractic Manipulative Treatment, 3 To 4 Spinal Regions

Modifier 1/Description:  GA - Waiver Of Liability Statement Issued As Required By Payer Policy, Individual Case

Modifier 2/Description:

Modifier 3/Description:

Modifier 4/Description:

Quantity Billed/Units:  1

Submitted Amount/Charges:  * Not Available *

Allowed Amount:  * Not Available *

Non-Covered:  * Not Available *

Place of Service/Description:  11 - Office

Type of Service/Description:  1 - Medical Care

Rendering Provider No:  123456

Rendering Provider NPI:  123456789



Line number:  2

Date of Service From:  12/01/2012

Date of Service To:  12/01/2012

Procedure Code/Description:  G0283 - Electrical Stimulation (Unattended), To One Or More Areas For Indication(S) Other Than Wound

Modifier 1/Description:  GY - Item Or Service Statutorily Excluded, Does Not Meet The Definition Of Any Medicare Benefit Or,

Modifier 2/Description:

Modifier 3/Description:

Modifier 4/Description:

Quantity Billed/Units:  1

Submitted Amount/Charges:  * Not Available *

Allowed Amount:  * Not Available *

Non-Covered:  * Not Available *

Place of Service/Description:  11 - Office

Type of Service/Description:  1 - Medical Care

Rendering Provider No:  123456

Rendering Provider NPI:  123456789



--------------------------------
Claim Lines for Claim Number: 123456789012

--------------------------------



Claim Type: Part D

Claim Number: 123456789012

Claim Service Date: 11/17/2011

Pharmacy / Service Provider: 123456789

Pharmacy Name: PHARMACY2 #00000

Drug Code: 00093013505

Drug Name: CARVEDILOL

Fill Number: 0

Days' Supply: 30

Prescriber Identifer: 123456789

Prescriber Name: Jane Doe



--------------------------------
Claim Lines for Claim Number: 123456789011

--------------------------------



Claim Type: Part D

Claim Number: 123456789011

Claim Service Date: 11/23/2011

Pharmacy / Service Provider: 1234567890

Pharmacy Name: PHARMACY3 #00000

Drug Code: 00781223310

Drug Name: OMEPRAZOLE

Fill Number: 4

Days' Supply: 30

Prescriber Identifer: 123456789

Prescriber Name: Jane Doe



--------------------------------



"""
