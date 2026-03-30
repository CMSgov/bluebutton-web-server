import json
import os
import requests
import logging
import django

# from apps.logging.request_logger import HHS_SERVER_LOGNAME_FMT

# logger = logging.getLogger(HHS_SERVER_LOGNAME_FMT.format(__name__))
django.setup()
# from apps.fhir.bluebutton.utils import FhirServerAuth

url = "https://sandbox.fhirv3.bfd.cmscloud.local/v3/fhir/Patient/$idi-match"
# json_file = "apps/fhir/bluebutton/tests/sample_requests/sample_requests/patient_match_all.json"
# json_file = "apps/fhir/bluebutton/tests/sample_requests/sample_requests/patient_match_case_1.json"
# json_file = "apps/fhir/bluebutton/tests/sample_requests/sample_requests/patient_match_case_4.json"
# json_file = "apps/fhir/bluebutton/tests/sample_requests/sample_requests/patient_match_case_8.json"
json_file = "apps/fhir/bluebutton/tests/sample_requests/no_patient_match.json" # Just changed the patient name to one that doesn't exist in the test data to simulate no patient match found scenario

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

# logger.debug("Request.post:%s" % url)
# logger.debug("Status of Request:%s" % response.status_code)
# logger.debug("Response JSON: %s" % response_json)
response_json = response.json()
print(response_json)
print(len(response_json['entry']))
response_json_entry = response_json['entry']

if response_json_entry and len(response_json_entry) > 1 and response_json['entry'][1]['resource']['resourceType'] == "Patient":
    # The length of the 'entry' list is greater than 1, which indicates a patient match was found and returned in the response
    # Return a token to the requester to indicate that a patient match was found
    # logger.debug("Patient match found")
    print("Patient match found")
else:
    # The length of the 'entry' list is 1, which indicates no patient match was found and no patient resource was returned in the response
    # Throw an error to indicate that no patient match was found
    print("No patient match found")
    # logger.debug("No patient match found")
