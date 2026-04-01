import json
import os
import requests

from apps.fhir.constants import MBI_URL, PATIENT_RESOURCE_TYPE

url = "https://sandbox.fhirv3.bfd.cmscloud.local/v3/fhir/Patient/$idi-match"
# json_file = "apps/fhir/bluebutton/tests/sample_requests/patient_match_all_request.json"
# json_file = "apps/fhir/bluebutton/tests/sample_requests/patient_match_case_1.json"
# json_file = "apps/fhir/bluebutton/tests/sample_requests/patient_match_case_4.json"
# json_file = "apps/fhir/bluebutton/tests/sample_requests/patient_match_case_8.json"
json_file = "apps/fhir/bluebutton/tests/sample_requests/no_patient_match_request.json" # Just changed the patient name to one that doesn't exist in the test data to simulate no patient match found scenario

headers = {
    "X-CLIENT-ID": "test-client-id",
    "X-CLIENT-NAME": "test-client-name",
    "X-CLIENT-IP": "test-client-ip"
}
# Get certs
certstore_path = os.environ['DJANGO_FHIR_CERTSTORE']
CERT="ca.cert.pem"
KEY="ca.key.nocrypt.pem"
cert=(f"{certstore_path}/{CERT}", f"{certstore_path}/{KEY}")

with open(json_file) as f:
    payload = json.load(f)

response = requests.post(url, headers=headers, json=payload, cert=cert, verify=False)
response_json = response.json()
print(response_json)

# The code below can probably be modified in the future to check for other resourceTypes besides patient, 
# but for now this is sufficient to determine if a patient match was found or not, 
# since the only resource that should be returned in the 'entry' list for a patient match call is a patient resource
def is_found(response_json):
    entries = response_json.get('entry', [])
    if not entries:
        # logger.debug("No 'entry' list in the response from BFD for patient_match call")
        return False
    if len(entries) > 1:
        patient = entries[1].get('resource', {})
        if patient.get('resourceType') == PATIENT_RESOURCE_TYPE:
            # The length of the 'entry' list is greater than 1, which indicates a patient match was found and returned in the response
            # logger.debug("Patient match found for patient_match call")
            return True
    else:
        # The length of the 'entry' list is 0 or 1, which indicates no patient match was found and no patient resource was returned 
        # logger.debug("No patient match found for patient_match call")
        return False
    
patient_found = is_found(response_json)
print(f"Patient match found: {patient_found}")

def extract_mbi(patient_bundle, index):
    """Safely extracts the ID from a patient entry in a mbi."""
    # Would be good to use fhir.resources library to parse the bundle and extract the patient resource and mbi, 
    # but for now this is a simple way to safely extract the id without risking exceptions being thrown that 
    # would need to be caught at higher levels in the call stack
    entries = patient_bundle.get('entry', [])
    
    # Check if index is valid
    if not(0 <= index < len(entries)):
        return None
    
    patient = entries[index].get('resource', {})
    
    # Look for the identifier with the MBI system and return the value 
    # (returns None if 'identifier' key is missing or if no identifier with the MBI system is found)
    identifiers = patient.get('identifier', [])
    for ident in identifiers:
        if ident.get('system') == MBI_URL and 'value' in ident:
            return ident.get('value')
    
    return None


mbi = extract_mbi(response_json, index=1)
print(f"Extracted MBI: {mbi}")

def extract_fhir_id(patient_bundle, index):
    """Safely extracts the ID from a patient entry in a FHIR Bundle."""
    # Would be good to use fhir.resources library to parse the bundle and extract the patient resource and id, 
    # but for now this is a simple way to safely extract the id without risking exceptions being thrown that 
    # would need to be caught at higher levels in the call stack
    entries = patient_bundle.get('entry', [])
    
def extract_fhir_id(patient_bundle, index):
    """Safely extracts the ID from a patient entry in a FHIR Bundle."""
    # Would be good to use fhir.resources library to parse the bundle and extract the patient resource and id, 
    # but for now this is a simple way to safely extract the id without risking exceptions being thrown that 
    # would need to be caught at higher levels in the call stack
    entries = patient_bundle.get('entry', [])
    
    # Check if index is valid
    if not(0 <= index < len(entries)):
        return None
    
    return entries[index].get('resource', {}).get('id')

fhir_id = extract_fhir_id(response_json, index=1)
print(f"Extracted FHIR ID: {fhir_id}")


    
