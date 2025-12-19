import json
import logging
from django.http import HttpRequest
from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from oauthlib.oauth2.rfc6749.errors import MissingTokenError, InvalidClientIdError
from requests_oauthlib import OAuth2Session
from urllib.parse import parse_qs, urlparse
from json import JSONDecodeError
from typing import Dict
import re
from collections import namedtuple

from waffle.decorators import waffle_switch

from .utils import (testclient_http_response_setup,
                    get_client_secret,
                    extract_page_nav,
                    _start_url_with_http_or_https)

from apps.dot_ext.loggers import cleanup_session_auth_flow_trace
from apps.fhir.bluebutton.views.home import (
    fhir_conformance_v1, fhir_conformance_v2, fhir_conformance_v3)
from apps.wellknown.views.openid import openid_configuration_v1, openid_configuration_v2, openid_configuration_v3

import apps.logging.request_logger as bb2logging

from apps.versions import Versions, VersionNotMatched

from apps.testclient.constants import (
    HOME_PAGE,
    RESULTS_PAGE,
    EndpointUrl,
    ResponseErrors
)

logger = logging.getLogger(bb2logging.HHS_SERVER_LOGNAME_FMT.format(__name__))

############################################################
# SUPPORT FUNCTIONS
############################################################


def _get_oauth2_session_with_token(request: HttpRequest) -> OAuth2Session:
    """Build an OAuth2 session object for making calls to the BFD/FHIR backend"""
    client_id = request.session['client_id']
    token = request.session['token']
    return OAuth2Session(client_id, token=token)


# Giving a name to the params. The patient is optional.
FhirDataParams = namedtuple("FhirDataParams", "name,uri,version,patient")


def _build_pagination_uri(uri: str, params: FhirDataParams, request: HttpRequest) -> str:
    # This sets up the navigation URI (pagination) based on whether we are handling
    # a patient or a beneficiary. All of this logic is essentially to add one parameter,
    # name correctly, to the nav URI. It is version dependent (there is no pagination in V3).
    # for now it's either EOB or Coverage, make this more generic later
    patient = request.GET.get('patient')
    beneficiary = request.GET.get('beneficiary')
    if patient is not None:
        id_type = 'patient'
        id = patient
    elif beneficiary is not None:
        id_type = 'beneficiary'
        id = beneficiary
    else:
        # We should not be able to get here.
        raise ValueError("Failed to set a patient id or beneficiary id on the pagination URI")  # noqa: E702

    # Extend the base URI with pagination information.
    uri = EndpointUrl.nav_uri(uri,
                              count=request.GET.get('_count', 10),
                              start_index=request.GET.get('startIndex', 0),
                              id_type=id_type,
                              id=id)
    return uri


def _get_fhir_data_as_json(request: HttpRequest, params: FhirDataParams) -> Dict[str, object]:
    """Make a call to the FHIR backend and return the JSON data from the call"""
    uri = EndpointUrl.fmt(params.name, params.uri, params.version, params.patient)

    if params.version in [Versions.V1, Versions.V2] and request.GET.get('nav_link', None):
        uri = _build_pagination_uri(uri, params, request)

    oath_session = _get_oauth2_session_with_token(request)
    r = oath_session.get(uri)

    try:
        result_json = r.json()
    except JSONDecodeError as err:
        result_json = {'error': f'Unrecoverable error fetching FHIR data: {err.msg}'}

    return result_json


def _convert_response_string_to_json(json_response: str) -> Dict[str, object]:
    """Converts a response string into a JSON object."""
    if json_response.status_code == 200:
        try:
            return json.loads(json_response.content)
        except JSONDecodeError:
            return {'error': f'Could not decode JSON; status code {json_response.status_code}'}  # noqa: E702
    else:
        # Same as above.
        return {'error': json_response.status_code}


def _get_oauth2_session_with_redirect(request: HttpRequest) -> OAuth2Session:
    client_id = request.session['client_id']
    redirect_uri = request.session['redirect_uri']
    return OAuth2Session(client_id, redirect_uri=redirect_uri)


def _pagination_info(request: HttpRequest, last_url: str, version=Versions.NOT_AN_API_VERSION) -> str:
    # with no total resource count of a bundle, use
    # backend pagination links for total page vs current page
    pg_info = 'No pagination info from backend'

    if version in [Versions.V1, Versions.V2]:
        cur_start_index = int(request.GET.get('startIndex', 0))
        pg_count = int(request.GET.get('_count', 10))
        qparams = parse_qs(urlparse(last_url).query)
        last_pg_index = qparams.get('startIndex', 0)
        if last_pg_index:
            last_pg_index = int(last_pg_index[0])
            current_index_display = cur_start_index // pg_count + 1
            last_index_display = last_pg_index // pg_count + 1
            pg_info = f'{current_index_display}/{last_index_display}'

    return pg_info


def _is_synthetic_patient_id(patient_id: str) -> bool:
    '''Checks if a string is a synthetic patient ID.
    '''
    return (
        patient_id is not None
        and patient_id.startswith('-')
        and re.match(r'^-\d+$', patient_id)
    )


############################################################
# ALL VERSIONS
############################################################

###############
# callback


@waffle_switch('enable_testclient')
def callback(request: HttpRequest):
    """Called when returning from authorizing as a beneficiary.

    When using the text client, users can authorize as a beneficiary as part of the auth workflow.

    https://bluebutton.cms.gov/developers/#authorization:~:text=Click-,Authorize%20as%20a%20Beneficiary,-.

    When they return from that workflow, the `callback` function (*this* function*) is called.

    If we make it through the function, we return a page with instructions for the developer to
    continue testing against the API (with httpie, Postman, code, etc.). There are also several
    links that provide examples of the Patient, Explanation of Benefits, etc. endpoints. Those URLs
    map to functions below (e.g. `test_patient_vX`).

    Args:
        request: A Django HttpRequest from the authorizing server
    Returns:
        redirect: Redirects to the `test_links` Django view.
    """

    # RESET TOKEN ON ERROR
    # If there was an error in the process (authorization denied, for example),
    # and there is a token in the session, we want to remove that token, redirect back to the page,
    # and in doing so, force re-authorization.
    if 'error' in request.GET:
        if 'token' in request.session:
            del request.session['token']
        return redirect('test_links', permanent=True)

    # We (mostly) trust the authorizing agent to send us a good URL.
    host = _start_url_with_http_or_https(settings.HOSTNAME_URL)
    auth_uri = host + request.get_full_path()
    token_uri = host

    # To guarantee that the `version` is a value, we provide a default for the `get`.
    # However, the default is `v0`, which is an invalid version. This keeps it of the
    # same type as valid values, but does not allow us to proceed if something has broken.
    version = request.session.get('api_ver', Versions.NOT_AN_API_VERSION)
    match version:
        case Versions.V1:
            token_uri += reverse('oauth2_provider:token')
        case Versions.V2:
            token_uri += reverse('oauth2_provider_v2:token-v2')
        case Versions.V3:
            token_uri += reverse('oauth2_provider_v3:token-v3')
        case _:
            logger.error(f"Failed to get valid API version back from authorizing agent. Given: [{version}]")
            return ResponseErrors.MissingCallbackVersionContext(version)

    oas = _get_oauth2_session_with_redirect(request)
    try:
        # Default the CV to '' if it is not part of the session.
        # This was an inline if, below. As written, it allowed '' as a code verifier.
        # It is not clear, now (2025) why it should be '' instead of `None`.
        # Perhaps oas.fetch_token fails (and raises a `MissingTokenError`) if the code verifier
        # cannot be pulled from the session.
        cv = request.session.get('code_verifier', '')
        token = oas.fetch_token(token_uri,
                                client_secret=get_client_secret(),
                                authorization_response=auth_uri,
                                code_verifier=cv)
    except MissingTokenError:
        token_uri = request.session['token_uri']
        logger.error(f'MissingToken: failed to get token from {token_uri}')
        return ResponseErrors.MissingTokenError(token_uri)
    except InvalidClientIdError as err:
        token_uri = request.session['token_uri']
        logger.error(f'InvalidClient: failed to get token from {token_uri}')
        logger.error(str(err))
        return ResponseErrors.InvalidClient(token_uri)

    # If we cannot find a patient id in the tokent, return an error.
    # If we find a non-synthetic id, return an error.
    # Otherwise, continue.
    patient_id = token.get('patient', None)
    if patient_id is None:
        return ResponseErrors.MissingPatientError()
    elif not _is_synthetic_patient_id(patient_id):
        # If we made it here, lets make sure we have a synthetic patient ID.
        # If we do not, then we need to clear the token and send back an error to the client.
        logmsg = 'Failed token is for a non-synthetic patient ID'
        logger.error(logmsg)
        if 'token' in request.session:
            del request.session['token']
        return ResponseErrors.NonSyntheticTokenError()

    # We are guaranteed at this point that the patient_id is not None, and it is a synthetic user id.
    request.session['token'] = token
    userinfo_uri = request.session['userinfo_uri']

    try:
        userinfo = oas.get(userinfo_uri).json()
    except Exception:
        userinfo = {'patient': patient_id}

    request.session['patient'] = userinfo.get('patient', patient_id)

    # This removes keys from the request object that we do not want to continue
    # carrying. It is code in `loggers.py`, which suggests that it... makes sure we do
    # not accidentally log values that might be privileged. The *reason* for this is not
    # captured in the code/docstring, but that is the *behavior*.
    cleanup_session_auth_flow_trace(request)

    # Successful token response, redirect to home page view
    return redirect('test_links', permanent=True)

###############
# restart


@waffle_switch('enable_testclient')
def restart(request: HttpRequest):
    '''We hit the `restart` case when a user clicks on the restart link on the API try-out page.'''
    if 'token' in request.session:
        del request.session['token']

    return render(request, HOME_PAGE, context={'session_token': None})


###############
# test_links

@waffle_switch('enable_testclient')
def test_links(request: HttpRequest, **kwargs):
    # New home page view consolidates separate success, error, and access denied views
    # If authorization was successful, pass token to template
    if 'token' in request.session:
        # In the event that we have a bad API version in the session, send them
        # back to the homepage.
        version = request.session.get('api_ver', Versions.NOT_AN_API_VERSION)
        match version:
            case Versions.NOT_AN_API_VERSION:
                # If somehow we ended up with a non-API version,
                # we return and clear the session token context.
                del request.session['token']
                return render(request, HOME_PAGE, context={'session_token': None})
            case Versions.V1:
                pass
            case Versions.V2:
                pass
            case Versions.V3:
                pass

        return render(request, HOME_PAGE,
                      context={
                          'session_token': request.session['token'],
                          'api_ver': version,
                      })
    else:
        # If we don't have a token, go back home.
        return render(request, HOME_PAGE, context={'session_token': None})

############################################################
# ENDPOINT LINKS
############################################################


def _link_session_or_version_is_bad(session, version):
    if 'token' not in session or version == Versions.NOT_AN_API_VERSION:
        return redirect('test_links', permanent=True)
    else:
        return False

###############
# authorize_link


def _authorize_link(request: HttpRequest, version=Versions.NOT_AN_API_VERSION):
    request.session.update(testclient_http_response_setup(version=version))

    oas = _get_oauth2_session_with_redirect(request)

    # We need scopes in V3.
    match version:
        case Versions.V1:
            pass
        case Versions.V2:
            pass
        case Versions.V3:
            # https://bluebutton.cms.gov/developers/#authorization:~:text=response%20type%3A%20code-,scope,-optional
            # Should the test client request all scopes for v3? Some scopes?
            oas.scope = "profile patient/Coverage.rs patient/Patient.rs patient/ExplanationOfBenefit.rs"
        case _:
            if 'token' in request.session:
                del request.session['token']
            return render(request, RESULTS_PAGE,
                          {'error': 'Invalid API version',
                           'response_type': 'BB2 error: authorize_link',
                           'api_ver': version
                           })

    authorization_url_kwargs = {}
    authorization_url_kwargs["code_challenge"] = request.session['code_challenge']
    authorization_url_kwargs["code_challenge_method"] = request.session['code_challenge_method']
    authorization_url = oas.authorization_url(
        request.session['authorization_uri'],
        request.session['state'],
        **authorization_url_kwargs
    )[0]

    return render(
        request,
        'authorize.html',
        {'authorization_url': authorization_url, 'api_ver': version}
    )

###############
# test_coverage


def _test_coverage(request: HttpRequest, version=Versions.NOT_AN_API_VERSION):
    if _link_session_or_version_is_bad(request.session, version):
        return _link_session_or_version_is_bad(request.session, version)

    coverage = _get_fhir_data_as_json(request, FhirDataParams(
        EndpointUrl.coverage, request.session['resource_uri'], version, None))

    nav_info, last_link = extract_page_nav(coverage)

    # _pagination_info is only returned for versions v1, v2
    # The string 'No pagination info from backend' is returned otherwise.
    if nav_info and len(nav_info) > 0:
        pg_info = _pagination_info(request, last_link, version)
    else:
        pg_info = None

    match version:
        case Versions.V1:
            url_name = 'test_coverage'
        case Versions.V2:
            url_name = 'test_coverage_v2'
        case Versions.V3:
            url_name = 'test_coverage_v3'
        case _:
            del request.session['token']
            return render(request, RESULTS_PAGE,
                          {'error': 'Invalid API version',
                           'response_type': 'BB2 error: test_coverage',
                           'api_ver': version
                           })

    return render(request,
                  RESULTS_PAGE,
                  {'fhir_json_pretty': json.dumps(coverage, indent=3),
                   'url_name': url_name,
                   'nav_list': nav_info,
                   'page_loc': pg_info,
                   'response_type': 'Bundle of Coverage',
                   'api_ver': version,
                   })

###############
# test_eob


def _test_eob(request: HttpRequest, version=Versions.NOT_AN_API_VERSION):
    if _link_session_or_version_is_bad(request.session, version):
        return _link_session_or_version_is_bad(request.session, version)

    params = FhirDataParams(EndpointUrl.explanation_of_benefit,
                            request.session['resource_uri'], version, None)

    eob = _get_fhir_data_as_json(request, params)

    nav_info, last_link = extract_page_nav(eob)

    # _pagination_info is only returned for versions v1, v2
    # The string 'No pagination info from backend' is returned otherwise.
    pg_info = _pagination_info(request, last_link, version) if nav_info and len(nav_info) > 0 else None

    match version:
        case Versions.V1:
            url_name = 'test_eob'
        case Versions.V2:
            url_name = 'test_eob_v2'
        case Versions.V3:
            url_name = 'test_eob_v3'
        case _:
            del request.session['token']
            return render(request, RESULTS_PAGE,
                          {'error': 'Invalid API version',
                           'response_type': 'BB2 error: test_eob',
                           'api_ver': version
                           })

    return render(request, RESULTS_PAGE,
                  {'fhir_json_pretty': json.dumps(eob, indent=3),
                   'url_name': url_name,
                   'nav_list': nav_info,
                   'page_loc': pg_info,
                   'response_type': 'Bundle of ExplanationOfBenefit',
                   'api_ver': version
                   })

###############
# test_metadata


def _test_metadata(request: HttpRequest, version=Versions.NOT_AN_API_VERSION):
    if _link_session_or_version_is_bad(request.session, version):
        return _link_session_or_version_is_bad(request.session, version)

    # Grab the conformance function that we'll use for
    # validating the FHIR JSON string.
    match version:
        case Versions.V1:
            conformance = fhir_conformance_v1
        case Versions.V2:
            conformance = fhir_conformance_v2
        case Versions.V3:
            conformance = fhir_conformance_v3
        case _:
            del request.session['token']
            return render(request, RESULTS_PAGE,
                          {'error': 'Invalid API version',
                           'response_type': 'BB2 error: test_metadata',
                           'api_ver': version
                           })

    json_response = _convert_response_string_to_json(conformance(request))

    return render(request, RESULTS_PAGE,
                  {'fhir_json_pretty': json.dumps(json_response, indent=3),
                   'response_type': 'FHIR Metadata',
                   'api_ver': version
                   })
###############
# test_openid_config


def _test_openid_config(request: HttpRequest, version=Versions.NOT_AN_API_VERSION):
    if _link_session_or_version_is_bad(request.session, version):
        return _link_session_or_version_is_bad(request.session, version)

    match version:
        case Versions.V1:
            json_response = _convert_response_string_to_json(openid_configuration_v1(request))
        case Versions.V2:
            json_response = _convert_response_string_to_json(openid_configuration_v2(request))
        case Versions.V3:
            json_response = _convert_response_string_to_json(openid_configuration_v3(request))
        case _:
            raise VersionNotMatched("Version not matched in openid_config.")

    return render(request, RESULTS_PAGE,
                  {'fhir_json_pretty': json.dumps(json_response, indent=3),
                   'response_type': 'OIDC Discovery',
                   'api_ver': version
                   })

###############
# test_patient


def _test_patient(request: HttpRequest, version=Versions.NOT_AN_API_VERSION):
    if _link_session_or_version_is_bad(request.session, version):
        return _link_session_or_version_is_bad(request.session, version)

    patient = _get_fhir_data_as_json(request, FhirDataParams(
        EndpointUrl.patient, request.session['resource_uri'], version, request.session['patient']))

    return render(request, RESULTS_PAGE,
                  {'fhir_json_pretty': json.dumps(patient, indent=3),
                   'response_type': 'Patient',
                   'api_ver': version
                   })

###############
# test_userinfo


def _test_userinfo(request: HttpRequest, version=Versions.NOT_AN_API_VERSION):
    if _link_session_or_version_is_bad(request.session, version):
        return _link_session_or_version_is_bad(request.session, version)

    user_info = _get_fhir_data_as_json(request, FhirDataParams(
        EndpointUrl.userinfo, request.session['resource_uri'], version, None))

    return render(request, RESULTS_PAGE,
                  {'fhir_json_pretty': json.dumps(user_info, indent=3),
                   'response_type': 'Profile (OIDC Userinfo)',
                   'api_ver': version
                   })


def _test_digital_insurance_card(request: HttpRequest, version=Versions.NOT_AN_API_VERSION):
    if _link_session_or_version_is_bad(request.session, version):
        return _link_session_or_version_is_bad(request.session, version)

    c4dic_info = _get_fhir_data_as_json(request, FhirDataParams(
        EndpointUrl.digital_insurance_card, request.session['resource_uri'], version, request.session['patient']))

    return render(request, RESULTS_PAGE,
                  {'fhir_json_pretty': json.dumps(c4dic_info, indent=3),
                   'response_type': 'Bundle',
                   'api_ver': version
                   })


############################################################
# VERSION 1
############################################################

###############
# authorize_link

@never_cache
@waffle_switch('enable_testclient')
def authorize_link_v1(request: HttpRequest):
    return _authorize_link(request, version=Versions.V1)

###############
# test_coverage


@never_cache
@waffle_switch('enable_testclient')
def test_coverage_v1(request: HttpRequest):
    return _test_coverage(request, version=Versions.V1)

###############
# test_eob


@never_cache
@waffle_switch('enable_testclient')
def test_eob_v1(request: HttpRequest):
    return _test_eob(request, version=Versions.V1)

###############
# test_metadata


@never_cache
@waffle_switch('enable_testclient')
def test_metadata_v1(request: HttpRequest):
    return _test_metadata(request, version=Versions.V1)


###############
# test_openid_config

@never_cache
@waffle_switch('enable_testclient')
def test_openid_config_v1(request: HttpRequest):
    return _test_openid_config(request, version=Versions.V1)

###############
# test_patient


@never_cache
@waffle_switch('enable_testclient')
def test_patient_v1(request: HttpRequest):
    return _test_patient(request, version=Versions.V1)

###############
# test_userinfo


@never_cache
@waffle_switch('enable_testclient')
def test_userinfo_v1(request: HttpRequest):
    return _test_userinfo(request, version=Versions.V1)


############################################################
# VERSION 2
############################################################

###############
# authorize_link

@never_cache
@waffle_switch('enable_testclient')
def authorize_link_v2(request: HttpRequest):
    return _authorize_link(request, version=Versions.V2)

###############
# test_coverage


@never_cache
@waffle_switch('enable_testclient')
def test_coverage_v2(request: HttpRequest):
    return _test_coverage(request, version=Versions.V2)

###############
# test_eob


@never_cache
@waffle_switch('enable_testclient')
def test_eob_v2(request: HttpRequest):
    return _test_eob(request, version=Versions.V2)

###############
# test_metadata


@never_cache
@waffle_switch('enable_testclient')
def test_metadata_v2(request: HttpRequest):
    return _test_metadata(request, version=Versions.V2)


###############
# test_openid_config

@never_cache
@waffle_switch('enable_testclient')
def test_openid_config_v2(request: HttpRequest):
    return _test_openid_config(request, version=Versions.V2)

###############
# test_patient


@never_cache
@waffle_switch('enable_testclient')
def test_patient_v2(request: HttpRequest):
    return _test_patient(request, version=Versions.V2)

###############
# test_userinfo


@never_cache
@waffle_switch('enable_testclient')
def test_userinfo_v2(request: HttpRequest):
    return _test_userinfo(request, version=Versions.V2)


############################################################
# VERSION 3
############################################################


###############
# authorize_link

@never_cache
@waffle_switch('enable_testclient')
def authorize_link_v3(request: HttpRequest):
    return _authorize_link(request, version=Versions.V3)

###############
# test_coverage


@never_cache
@waffle_switch('enable_testclient')
def test_coverage_v3(request: HttpRequest):
    return _test_coverage(request, version=Versions.V3)

###############
# test_eob


@never_cache
@waffle_switch('enable_testclient')
def test_eob_v3(request: HttpRequest):
    return _test_eob(request, version=Versions.V3)

###############
# test_metadata


@never_cache
@waffle_switch('enable_testclient')
def test_metadata_v3(request: HttpRequest):
    return _test_metadata(request, version=Versions.V3)


###############
# test_openid_config

@never_cache
@waffle_switch('enable_testclient')
def test_openid_config_v3(request: HttpRequest):
    return _test_openid_config(request, version=Versions.V3)

###############
# test_patient


@never_cache
@waffle_switch('enable_testclient')
def test_patient_v3(request: HttpRequest):
    return _test_patient(request, version=Versions.V3)

###############
# test_userinfo


@never_cache
@waffle_switch('enable_testclient')
def test_userinfo_v3(request: HttpRequest):
    return _test_userinfo(request, version=Versions.V3)


@never_cache
@waffle_switch('enable_testclient')
def test_digital_insurance_card_v3(request: HttpRequest):
    return _test_digital_insurance_card(request, version=Versions.V3)
