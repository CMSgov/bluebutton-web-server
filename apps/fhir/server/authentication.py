import requests
import logging
from rest_framework import exceptions
from ..bluebutton.exceptions import UpstreamServerException
from ..bluebutton.utils import (FhirServerAuth,
                                get_resourcerouter)

logger = logging.getLogger('hhs_server.%s' % __name__)


def authenticate_crosswalk(crosswalk):
    auth_state = FhirServerAuth(None)
    certs = (auth_state['cert_file'], auth_state['key_file'])

    # URL for patient ID.
    url = get_resourcerouter().fhir_url + \
        "Patient/?identifier=http%3A%2F%2Fbluebutton.cms.hhs.gov%2Fidentifier%23hicnHash%7C" + \
        crosswalk.user_id_hash + \
        "&_format=json"
    response = requests.get(url, cert=certs, verify=False)
    backend_data = response.json()

    if 'entry' in backend_data and backend_data['total'] == 1:
        fhir_id = backend_data['entry'][0]['resource']['id']
        crosswalk.fhir_id = fhir_id
        crosswalk.save()

        logger.info("Success:Beneficiary connected to FHIR")
        # Recheck perms
    else:
        if backend_data.get('total', 0) > 1:
            # Don't return a 404 because retrying later will not fix this.
            raise UpstreamServerException("Duplicate beneficiaries found")

        raise exceptions.NotFound("The requested Beneficiary has no entry, however this may change")

    return backend_data
