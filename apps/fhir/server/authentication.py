import requests
import os
from urllib.parse import quote
from typing import NamedTuple, Optional

from apps.versions import Versions
from apps.dot_ext.loggers import get_session_auth_flow_trace
from apps.fhir.bluebutton.signals import (
    pre_fetch,
    post_fetch
)
from apps.fhir.constants import FHIR_POST_SEARCH_PARAM_IDENTIFIER_HICN_HASH, FHIR_PATIENT_SEARCH_PARAM_IDENTIFIER_MBI
from apps.fhir.bluebutton.utils import (generate_info_headers,
                                        set_default_header)

from apps.fhir.bluebutton.exceptions import UpstreamServerException
from apps.fhir.bluebutton.utils import FhirServerAuth
from apps.fhir.server.settings import fhir_settings
from apps.fhir.server.loggers import log_match_fhir_id
from waffle import switch_is_active


def search_fhir_id_by_identifier_mbi(mbi, request=None, version=Versions.NOT_AN_API_VERSION):
    """
        Search the backend FHIR server's patient resource
        using the mbi identifier.
    """
    search_identifier = f"{FHIR_PATIENT_SEARCH_PARAM_IDENTIFIER_MBI}|{mbi}"
    return search_fhir_id_by_identifier(search_identifier, request, version)


def search_fhir_id_by_identifier_hicn_hash(hicn_hash, request=None, version=Versions.NOT_AN_API_VERSION):
    """
        Search the backend FHIR server's patient resource
        using the hicn_hash identifier.
    """
    search_identifier = f"{FHIR_POST_SEARCH_PARAM_IDENTIFIER_HICN_HASH}|{hicn_hash}"
    return search_fhir_id_by_identifier(search_identifier, request, version)


def search_fhir_id_by_identifier(search_identifier, request=None, version=Versions.NOT_AN_API_VERSION):
    """Search the backend FHIR server's patient resource using the specified identifier.

    Args:
        search_identifier (str): the identifier to search for
        request (_type_, optional): _description_. Defaults to None.
        version (Version): version of BFD to check. Defaults to Versions.NOT_AN_API_VERSION.

    Raises:
        UpstreamServerException: For backend response issues.
        e: exception to raise

    Returns:
        fhir_id (str): matched ID (or None for no match)
    """
    # Get certs from FHIR server settings
    auth_settings = FhirServerAuth()
    certs = (auth_settings['cert_file'], auth_settings['key_file'])
    # Add headers for FHIR backend logging, including auth_flow_dict
    if request:
        # Get auth flow session values.
        auth_flow_dict = get_session_auth_flow_trace(request)
        headers = generate_info_headers(request, version)
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

    # Build URL based on BFD version
    ver = f'v{version}'

    fhir_url = fhir_settings.fhir_url
    if ver == 'v3' and fhir_settings.fhir_url_v3:
        fhir_url = fhir_settings.fhir_url_v3
    url = f"{fhir_url}/{ver}/fhir/Patient/_search"

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
        except requests.exceptions.HTTPError as e:
            raise UpstreamServerException(e)
        except requests.exceptions.SSLError as e:
            if retries < max_retries and (env is None or env == 'local'):
                # Checking target_env ensures the retry logic only happens on local
                retries += 1
            else:
                raise e


class MatchFhirIdLookupType:
    """Constants for FHIR ID lookup method"""
    MBI = 'M'
    HICN_HASH = 'H'


class MatchFhirIdErrorType:
    """Constants for error types in MatchFhirIdResult"""
    UPSTREAM = 'upstream'
    NOT_FOUND = 'not_found'


class MatchFhirIdResult(NamedTuple):
    """Result of attempting to match a FHIR ID"""
    fhir_id: Optional[str] = None
    lookup_type: MatchFhirIdLookupType = MatchFhirIdLookupType.MBI
    error: Optional[str] = None
    error_type: Optional[MatchFhirIdErrorType] = None  # 'upstream', 'not_found', etc.


def match_fhir_id(mbi, hicn_hash, request=None, version=Versions.NOT_AN_API_VERSION) -> MatchFhirIdResult:
    """Matches a patient identifier via the backend FHIR server using an MBI or HICN hash.
        - Perform primary lookup using mbi.
        - If there is an mbi lookup issue, raise exception.
        - Perform secondary lookup using HICN_HASH
        - If there is a hicn_hash lookup issue, raise exception.
        - A NotFound exception is raised, if no match was found.

      Args:
        mbi (string): the mbi of the user
        hicn_hash (string): the hashed hicn of the user
        version (int): Current API version for this call
        request (HttpRequest, optional): the Django request

      Returns:
        MatchFhirIdResult: A NamedTuple with the following fields:
            fhir_id (Optional[str]): The matched FHIR ID, if found
            lookup_type (Optional[LookupType]): The type of lookup used to find the FHIR ID
            error (Optional[str]): Error message if the match was not successful
            error_type (Optional[str]): Type of error if the match was not successful

      Raises:
        UpstreamServerException: If hicn_hash or mbi search found duplicates.
        NotFound: If both searches did not match a fhir_id.
    """
    # Don't do v3 BFD lookups if the v3 switch isn't enabled to allow us to prevent extra errors in logs
    if not switch_is_active('v3_endpoints') and version == Versions.V3:
        log_match_fhir_id(request, version, None, hicn_hash, False, 'M', "Server settings don't enable v3 lookups.")
        return MatchFhirIdResult(
            error='This server\'s settings do not allow lookups of v3 ids',
            error_type=MatchFhirIdErrorType.NOT_FOUND,
            lookup_type=MatchFhirIdLookupType.MBI
        )

    # Perform primary lookup using MBI
    if mbi:
        try:
            fhir_id = search_fhir_id_by_identifier_mbi(mbi, request, version)
        except UpstreamServerException as err:
            log_match_fhir_id(request, version, None, hicn_hash, False, 'M', str(err))
            # Don't return a 404 because retrying later will not fix this.
            return MatchFhirIdResult(
                error=str(err.detail),
                error_type=MatchFhirIdErrorType.UPSTREAM,
                lookup_type=MatchFhirIdLookupType.MBI
            )

        if fhir_id:
            # Found beneficiary!
            log_match_fhir_id(request, version, fhir_id, hicn_hash, True, 'M',
                              'FOUND beneficiary via user_mbi')
            return MatchFhirIdResult(
                fhir_id=fhir_id,
                lookup_type=MatchFhirIdLookupType.MBI
            )

    # Perform secondary lookup using HICN_HASH
    # WE CANNOT DO A HICN HASH LOOKUP FOR V3, but there are tests that rely on a null MBI
    # and populated hicn_hash, which now execute on v3 (due to updates in __get_and_update_user)
    # so we need to leave this conditional as is for now, until the test is modified and/or hicn_hash is removed
    # if version in [Versions.V1, Versions.V2] and hicn_hash:
    if hicn_hash and version != Versions.V3:
        try:
            fhir_id = search_fhir_id_by_identifier_hicn_hash(hicn_hash, request, version)
        except UpstreamServerException as err:
            log_match_fhir_id(request, version, None, hicn_hash, False, 'H', str(err))
            return MatchFhirIdResult(
                error=str(err.detail),
                error_type=MatchFhirIdErrorType.UPSTREAM,
                lookup_type=MatchFhirIdLookupType.HICN_HASH
            )

        if fhir_id:
            log_match_fhir_id(request, version, fhir_id, hicn_hash, True, 'H',
                              'FOUND beneficiary via hicn_hash')
            return MatchFhirIdResult(
                fhir_id=fhir_id,
                lookup_type=MatchFhirIdLookupType.HICN_HASH
            )

    log_match_fhir_id(request, version, None, hicn_hash, False, None, 'FHIR ID NOT FOUND for both mbi and hicn_hash')
    return MatchFhirIdResult(
        error='The requested Beneficiary has no entry, however this may change',
        error_type=MatchFhirIdErrorType.NOT_FOUND,
        lookup_type=MatchFhirIdLookupType.MBI
    )


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
