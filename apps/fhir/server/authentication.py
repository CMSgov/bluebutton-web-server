import requests
import os
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

    max_retries = 3
    retries = 0
    env = os.environ.get('TARGET_ENV')
    while retries <= max_retries:
        try:
            s = requests.Session()
            payload = {"identifier": search_identifier}
            req = requests.Request('POST', url, headers=headers, data=payload)
            prepped = req.prepare()
            pre_fetch.send_robust(FhirServerAuth, request=req, auth_request=request, api_ver=ver)
            response = s.send(prepped, cert=certs, verify=False)
            post_fetch.send_robust(FhirServerAuth, request=req, auth_request=request, response=response, api_ver=ver)
            response.raise_for_status()
            backend_data = response.json()
            # Parse and validate backend_data (bundle of patients) response.
            fhir_id, err_detail = _validate_patient_search_result(backend_data)
            if err_detail is not None:
                raise UpstreamServerException(err_detail)
            return fhir_id
        except requests.exceptions.SSLError as e:
            if retries < max_retries and (env is None or env == 'DEV'):
                # Checking target_env ensures the retry logic only happens on local
                print(f"FHIR ID search request failed. Retrying... ({retries+1}/{max_retries})")
                retries += 1
            else:
                raise e


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


def _validate_patient_search_result(bundle_of_patients):
    '''
    helper to check the bundle of patient(s), expecting one and only one patient
    input: patient search result - bundle of patients
    return: fhir_id, err_detail
    '''
    fhir_id = None
    err_detail = None
    if bundle_of_patients:
        if bundle_of_patients.get('resourceType') == "Bundle":
            entries = bundle_of_patients.get('entry')
            if entries:
                if len(entries) > 1:
                    err_detail = "Duplicate beneficiaries found in Patient resource bundle."
                else:
                    # further validate the only entry is Patient and its id is there,
                    # see Patient resource excerpt below for reference:
                    # {
                    #     "resourceType": "Patient",
                    #     "id": "-10000010254618",
                    #     "meta": {
                    #         "lastUpdated": "2023-06-14T18:17:07.293+00:00",
                    #         "profile": [
                    #             "http://hl7.org/fhir/us/carin-bb/StructureDefinition/C4BB-Patient"
                    #         ]
                    #     },
                    #     "extension": [
                    #         {
                    #            ...............
                    #
                    pt = entries[0].get("resource")
                    if pt:
                        rs_type = pt.get('resourceType', "")
                        fhir_id = pt.get('id')
                        if rs_type == "Patient":
                            if fhir_id:
                                # Found a single matching ID (fhir_id).
                                pass
                            else:
                                err_detail = ("Unexpected in Patient search: malformed Patient resource"
                                              "- missing id attribute or id value empty.")
                        else:
                            err_detail = ("Unexpected in Patient search: expect Patient resource,"
                                          " got 'resourceType': {}.").format(rs_type)
                    else:
                        err_detail = "Unexpected in Patient search: expect a resource, got None."
            else:
                # No patient match, not found - this leads to fhir_id = None and err_detail = None return to caller
                # this else branch can be removed but keep it explicit for readability
                pass
        else:
            err_detail = ("Unexpected in Patient search:"
                          " expected result of 'resourceType': Bundle, got {}").format(bundle_of_patients.get('resourceType'))
    else:
        # Unexpected result, response json from back end is None
        err_detail = "Unexpected in Patient search: response json is None."

    return fhir_id, err_detail
