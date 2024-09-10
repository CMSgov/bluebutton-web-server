import requests

from django.conf import settings
from rest_framework import exceptions
from urllib.parse import quote

from apps.dot_ext.loggers import get_session_auth_flow_trace
from apps.fhir.bluebutton.signals import (
    pre_fetch,
    post_fetch
)
from apps.fhir.bluebutton.utils import (generate_info_headers,
                                        set_default_header)

from ..bluebutton.exceptions import UpstreamServerException
from ..bluebutton.utils import (FhirServerAuth,
                                get_resourcerouter)
from .loggers import log_match_fhir_id


def search_fhir_id_by_identifier_mbi(mbi, request=None):
    """
        Search the backend FHIR server's patient resource
        using the mbi_hash identifier.
    """
    search_identifier = f"{settings.FHIR_PATIENT_SEARCH_PARAM_IDENTIFIER_MBI}|{mbi}"

    return search_fhir_id_by_identifier(search_identifier, request)


def search_fhir_id_by_identifier_hicn_hash(hicn_hash, request=None):
    """
        Search the backend FHIR server's patient resource
        using the hicn_hash identifier.
    """
    search_identifier = f"{settings.FHIR_POST_SEARCH_PARAM_IDENTIFIER_HICN_HASH}|{hicn_hash}"

    return search_fhir_id_by_identifier(search_identifier, request)


def search_fhir_id_by_identifier(search_identifier, request=None):
    """
        Search the backend FHIR server's patient resource
        using the specified identifier.

        Return:  fhir_id = matched ID (or None for no match).

        Raises exception:
            UpstreamServerException: For backend response issues.
    """
    # Get certs from FHIR server settings
    auth_settings = FhirServerAuth(None)
    certs = (auth_settings['cert_file'], auth_settings['key_file'])

    # Add headers for FHIR backend logging, including auth_flow_dict
    if request:
        # Get auth flow session values.
        auth_flow_dict = get_session_auth_flow_trace(request)
        headers = generate_info_headers(request)
        headers = set_default_header(request, headers)
        # may be part of the contract with BFD
        headers['BlueButton-AuthUuid'] = auth_flow_dict.get('auth_uuid', '')
        headers['BlueButton-AuthAppId'] = auth_flow_dict.get('auth_app_id', '')
        headers['BlueButton-AuthAppName'] = auth_flow_dict.get('auth_app_name', '')
        # BB2-2011 update logging w.r.t new fields application data_access_type
        headers['BlueButton-AuthAppDataAccessType'] = auth_flow_dict.get('auth_app_data_access_type', '')
        headers['BlueButton-AuthAppEndDate'] = auth_flow_dict.get('auth_app_end_date', '')

        # BB2-1544: header value with char (>256) choke the header put in underlying request prep
        try:
            headers['BlueButton-AuthAppName'].encode('latin1')
        except UnicodeEncodeError:
            headers['BlueButton-AuthAppName'] = quote(headers['BlueButton-AuthAppName'])

        headers['BlueButton-AuthClientId'] = auth_flow_dict.get('auth_client_id', '')
    else:
        headers = None

    # Build URL with patient ID search by identifier.
    ver = "v{}".format(request.session.get('version', 1))
    url = f"{get_resourcerouter().fhir_url}/{ver}/fhir/Patient/_search"
    s = requests.Session()

    payload = {"identifier": search_identifier}
    req = requests.Request('POST', url, headers=headers, data=payload)
    prepped = req.prepare()
    pre_fetch.send_robust(FhirServerAuth, request=req, auth_request=request, api_ver=ver)
    response = s.send(prepped, cert=certs, verify=False)
    post_fetch.send_robust(FhirServerAuth, request=req, auth_request=request, response=response, api_ver=ver)
    response.raise_for_status()
    backend_data = response.json()

    # Parse and validate backend_data response.
    if (
        'total' in backend_data
            and backend_data.get('total', 0) == 1
            and 'entry' in backend_data
            and isinstance(backend_data.get('entry', False), list)
            and len(backend_data.get('entry', '')) == 1
            and isinstance(backend_data['entry'][0].get('resource', False), dict)
            and isinstance(backend_data['entry'][0]['resource'].get('resourceType', False), str)
            and backend_data['entry'][0]['resource']['resourceType'] == "Patient"
            and isinstance(backend_data['entry'][0]['resource'].get('id', False), str)
            and len(backend_data['entry'][0]['resource']['id']) > 0
    ):
        # Found a single matching ID.
        fhir_id = backend_data['entry'][0]['resource']['id']
        return fhir_id
    elif (
        'total' in backend_data
            and 'entry' in backend_data
            and (backend_data.get('total', 0) > 1 or len(backend_data.get('entry', '')) > 1)
    ):
        # Has duplicate beneficiary IDs.
        raise UpstreamServerException("Duplicate beneficiaries found in Patient resource bundle")
    elif (
        'total' in backend_data
            and 'entry' not in backend_data
            and backend_data.get('total', -1) == 0
    ):
        # Not found.
        return None
    else:
        # Unexpected result! Something weird is happening?
        raise UpstreamServerException("Unexpected result found in the Patient resource bundle")


def match_fhir_id(mbi, mbi_hash, hicn_hash, request=None):
    """
      Matches a patient identifier via the backend FHIR server
      using an MBI or HICN hash.

      Summary:
        - Perform primary lookup using mbi_hash.
        - If there is an mbi_hash lookup issue, raise exception.
        - Perform secondary lookup using HICN_HASH
        - If there is a hicn_hash lookup issue, raise exception.
        - A NotFound exception is raised, if no match was found.
      Returns:
        fhir_id = Matched patient identifier.
        hash_lookup_type = The type used for the successful lookup (M or H).
      Raises exceptions:
        UpstreamServerException: If hicn_hash or mbi search found duplicates.
        NotFound: If both searches did not match a fhir_id.
    """
    # Perform primary lookup using MBI
    if mbi:
        try:
            fhir_id = search_fhir_id_by_identifier_mbi(mbi, request)
        except UpstreamServerException as err:
            log_match_fhir_id(request, None, mbi_hash, hicn_hash, False, "M", str(err))
            # Don't return a 404 because retrying later will not fix this.
            raise UpstreamServerException(err.detail)

        if fhir_id:
            # Found beneficiary!
            log_match_fhir_id(request, fhir_id, mbi_hash, hicn_hash, True, "M",
                              "FOUND beneficiary via mbi_hash")
            return fhir_id, "M"

    # Perform secondary lookup using HICN_HASH
    try:
        fhir_id = search_fhir_id_by_identifier_hicn_hash(hicn_hash, request)
    except UpstreamServerException as err:
        log_match_fhir_id(request, None, mbi_hash, hicn_hash, False, "H", str(err))
        # Don't return a 404 because retrying later will not fix this.
        raise UpstreamServerException(err.detail)

    if fhir_id:
        # Found beneficiary!
        log_match_fhir_id(request, fhir_id, mbi_hash, hicn_hash, True, "H",
                          "FOUND beneficiary via hicn_hash")
        return fhir_id, "H"
    else:
        log_match_fhir_id(request, fhir_id, mbi_hash, hicn_hash, False, None,
                          "FHIR ID NOT FOUND for both mbi_hash and hicn_hash")
        raise exceptions.NotFound("The requested Beneficiary has no entry, however this may change")
