import requests
import logging
from django.conf import settings
import urllib.parse
from rest_framework import exceptions
from ..bluebutton.exceptions import UpstreamServerException
from ..bluebutton.utils import (FhirServerAuth,
                                get_resourcerouter)

logger = logging.getLogger('hhs_server.%s' % __name__)

FHIR_URL_FORMATTER = "{}Patient/?{}|{}&_format=application/json+fhir"


def match_pt_id_hash(id_hash, id_type):
    auth_state = FhirServerAuth(None)
    certs = (auth_state['cert_file'], auth_state['key_file'])
    # URL for patient ID.
    if id_type == 'H':
        id_param_type = settings.FHIR_PAT_ID_SEARCH_PARAM_HICN
    elif id_type == 'M':
        id_param_type = settings.FHIR_PAT_ID_SEARCH_PARAM_MBI
    else:
        id_param_type = settings.FHIR_PAT_ID_SEARCH_PARAM_BEN

    sys_uri = settings.FHIR_PAT_ID_SYS_URI + id_param_type
    url = FHIR_URL_FORMATTER.format(get_resourcerouter().fhir_url, 
        urllib.parse.urlencode({'identifier': sys_uri}, doseq=True), id_hash)
    response = requests.get(url, cert=certs, verify=False)
    response.raise_for_status()
    backend_data = response.json()

    if backend_data.get('total', 0) > 1:
        # Don't return a 404 because retrying later will not fix this.
        raise UpstreamServerException("Duplicate beneficiaries found")

    if 'entry' in backend_data and len(backend_data['entry']) > 1:
        raise UpstreamServerException("Duplicate beneficiaries found")

    if 'entry' in backend_data and backend_data['total'] == 1:
        fhir_id = backend_data['entry'][0]['resource']['id']
        return fhir_id, backend_data

    logger.info({
        "type": "FhirIDNotFound",
        "bene_id/hicn_hash/mbi_hash": id_hash,
        "id_hash_type": id_param_type,
    })
    raise exceptions.NotFound("The requested Beneficiary has no entry, however this may change")
