import requests
import logging
from rest_framework import exceptions
from ..bluebutton.exceptions import UpstreamServerException
from ..bluebutton.utils import (FhirServerAuth,
                                get_resourcerouter)

logger = logging.getLogger('hhs_server.%s' % __name__)


def match_hicn_hash(hicn_hash):
    auth_state = FhirServerAuth(None)
    certs = (auth_state['cert_file'], auth_state['key_file'])
    # URL for patient ID.
    url = get_resourcerouter().fhir_url + \
        "Patient/?identifier=http%3A%2F%2Fbluebutton.cms.hhs.gov%2Fidentifier%23hicnHash%7C" + \
        hicn_hash + \
        "&_format=json"
    response = requests.get(url, cert=certs, verify=False)
    response.raise_for_status()
    backend_data = response.json()

    if backend_data.get('total', 0) > 1:
        # Don't return a 404 because retrying later will not fix this.
        raise UpstreamServerException("Duplicate beneficiaries found")

    if 'entry' in backend_data and backend_data['total'] == 1:
        fhir_id = backend_data['entry'][0]['resource']['id']
        return fhir_id, backend_data

    raise exceptions.NotFound("The requested Beneficiary has no entry, however this may change")


def authenticate_crosswalk(crosswalk):
    fhir_id, backend_data = match_hicn_hash(crosswalk.user_id_hash)

    crosswalk.fhir_id = fhir_id
    crosswalk.save()

    return backend_data
