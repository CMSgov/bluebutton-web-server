#! /usr/bin/env bash

X-CLIENT-ID="test-client-id"
X-CLIENT-NAME="test-client-name"
X-CLIENT-IP="test-client-ip"

source dev-local/.env.local

# Need to replace <my_id> with the actual user ID on the machine running this script.
xh -v POST "https://sandbox.fhirv3.bfd.cmscloud.local/v3/fhir/Patient/\$idi-match" \
    X-CLIENT-ID:${X-CLIENT-ID} \
    X-CLIENT-NAME:${X-CLIENT-NAME} \
    X-CLIENT-IP:${X-CLIENT-IP} \
    @apps/fhir/bluebutton/tests/sample_requests/patient_match_all_request.json \
    --cert ${BB2_CERTSTORE_PATH}/ca.cert.pem \
    --cert-key ${BB2_CERTSTORE_PATH}/ca.key.nocrypt.pem \
    --verify=no

