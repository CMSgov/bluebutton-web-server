import json
import logging
from django.http import HttpRequest
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from oauthlib.oauth2.rfc6749.errors import MissingTokenError
from requests_oauthlib import OAuth2Session
from rest_framework import status
from urllib.parse import parse_qs, urlparse
from json import JSONDecodeError
from typing import Dict

from waffle.decorators import waffle_switch

from .utils import test_setup, get_client_secret, extract_page_nav
from apps.dot_ext.loggers import cleanup_session_auth_flow_trace
from apps.fhir.bluebutton.views.home import (
    fhir_conformance_v1, fhir_conformance_v2, fhir_conformance_v3)
from apps.wellknown.views.openid import openid_configuration

import apps.logging.request_logger as bb2logging

from apps.constants import Versions

from apps.testclient.constants import (
    HOME_PAGE,
    RESULTS_PAGE,
    ENDPOINT_URL_FMT,
    NAV_URI_FMT
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


# QUESTION MCJ: Should this have a more descriptive name? get_fhir_json_from_backend?
def _get_data_json(request: HttpRequest, name: str, params: list[str, str]) -> Dict[str, object]:
    """Make a call to the FHIR backend and return the JSON data from the call"""

    nav_link = request.GET.get('nav_link', None)

    # TODO: Do I want this to be a function?
    uri = ENDPOINT_URL_FMT[name].format(*params)

    if nav_link is not None:
        q_params = [uri]
        q_params.append(request.GET.get('_count', 10))
        q_params.append(request.GET.get('startIndex', 0))

        # for now it's either EOB or Coverage, make this more generic later
        patient = request.GET.get('patient')

        if patient is not None:
            q_params.append('patient')
            q_params.append(patient)

        beneficiary = request.GET.get('beneficiary')

        if beneficiary is not None:
            q_params.append('beneficiary')
            q_params.append(beneficiary)

        uri = NAV_URI_FMT.format(*q_params)

    oas = _get_oauth2_session_with_token(request)
    r = oas.get(uri)
    return r.json()


def _convert_response_string_to_json(json_response: str) -> Dict[str, object]:
    """Converts a response string into a JSON object."""
    if json_response.status_code == 200:
        try:
            return json.loads(json_response.content)
        except JSONDecodeError:
            return {'error': f'Could not decode JSON; status code {json_response.status_code}'}
    else:
        return {'error': json_response.status_code}


def _get_oauth2_session_with_redirect(request: HttpRequest) -> OAuth2Session:
    client_id = request.session['client_id']
    redirect_uri = request.session['redirect_uri']
    return OAuth2Session(client_id, redirect_uri=redirect_uri)


def _pagination_info(request: HttpRequest, last_url: str) -> str:
    # with no total resource count of a bundle, use
    # backend pagination links for total page vs current page
    cur_start_index = int(request.GET.get('startIndex', 0))
    pg_count = int(request.GET.get('_count', 10))
    qparams = parse_qs(urlparse(last_url).query)
    last_pg_index = qparams.get('startIndex', 0)

    pg_info = 'No pagination info from backend'

    if last_pg_index:
        last_pg_index = int(last_pg_index[0])
        current_index_display = cur_start_index // pg_count + 1
        last_index_display = last_pg_index // pg_count + 1
        pg_info = f'{current_index_display}/{last_index_display}'

    return pg_info


def _is_synthetic_patient_id(patient_id: str) -> bool:
    """Tells us if a beneficiary ID is synthetic"""
    return patient_id is not None and not patient_id.startswith('-')

############################################################
# ALL VERSIONS
############################################################

###############
# callback


@waffle_switch('enable_testclient')
def callback(request: HttpRequest):
    # Authorization has been denied or another error has occured, remove token if existing
    # and redirect to home page view to force re-authorization
    if 'error' in request.GET:
        if 'token' in request.session:
            del request.session['token']
        return redirect('test_links', permanent=True)

    oas = _get_oauth2_session_with_redirect(request)

    host = settings.HOSTNAME_URL

    if not (host.startswith('http://') or host.startswith('https://')):
        host = f'https://{host}'

    auth_uri = host + request.get_full_path()
    token_uri = host

    # TODO: Make the version pathways version specific
    # FIXME: Should this be... our default API version as opposed to v1?
    # This was 'v1', which I've turned into a constant... but, I don't know if we should
    # instead be using the DEFAULT constant instead as we make this change.
    # DECISION: I'm going to make sure we have a value, but it will cause things to fail.
    # The callback should always have an `api_ver` as a parameter; therefore, we should
    # not default down to (say) v1 or v2.
    version = request.session.get('api_ver', Versions.NOT_AN_API_VERSION)
    match version:
        case Versions.V1:
            # QUESTION MCJ: Is this even possible? I think we determined that the v1
            # pathway was not possible. This is also problematic for a v3 pathway.
            token_uri += reverse('oauth2_provider:token')
        case Versions.V2:
            token_uri += reverse('oauth2_provider_v2:token-v2')
        case Versions.V3:
            # TODO add v3 pathway
            # Simply break for now.
            raise
        case _:
            # TODO RAISE EXCEPTION
            pass

    try:
        # Default the CV to '' if it is not part of the session;
        # This was an inline if, below. Not sure why it should be '' instead of None.
        cv = request.session.get('code_verifier', '')
        token = oas.fetch_token(token_uri,
                                client_secret=get_client_secret(),
                                authorization_response=auth_uri,
                                code_verifier=cv)
    except MissingTokenError:
        logmsg = 'Failed to get token from %s' % (request.session['token_uri'])
        logger.error(logmsg)
        return JsonResponse({'error': 'Failed to get token from',
                             'code': 'MissingTokenError',
                             'help': 'Try authorizing again.'},
                            status=500)

    # For test client allow only authorize on synthetic beneficiaries
    patient_id = token.get('patient', None)
    if _is_synthetic_patient_id(patient_id):
        logger.error(f'Failed token is for a non-synthetic patient ID = {patient_id}')
        if 'token' in request.session:
            del request.session['token']
        return JsonResponse({'error': logmsg,
                             'code': 'NonSyntheticTokenError',
                             'help': 'Try authorizing again.'
                             },
                            status=status.HTTP_403_FORBIDDEN)

    # MCJ: At this point, the patient_id could still be None.
    # The if, above, is both "is it not none, AND does it not start with a negative?"
    # Therefore, it could... be None.

    request.session['token'] = token

    userinfo_uri = request.session['userinfo_uri']
    try:
        userinfo = oas.get(userinfo_uri).json()
    except Exception:
        # MCJ: This does not make sense. If we failed to do a good get above,
        # we now... could be setting the patient_id to None.
        userinfo = {'patient': patient_id}

    # QUESTION MCJ: Why can we get here with None as the patient_id? We should bail sooner.
    # This allows us to set the session['patient'] to None.
    request.session['patient'] = userinfo.get('patient', patient_id)

    # We are done using auth flow trace, clear from the session.
    # MCJ: WAT
    cleanup_session_auth_flow_trace(request)

    # Successful token response, redirect to home page view
    return redirect('test_links', permanent=True)

###############
# restart


@waffle_switch('enable_testclient')
def restart(request: HttpRequest):
    """We hit the `restart` case when a user clicks on the restart link on the API try-out page."""
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
        return render(request, HOME_PAGE,
                      context={'session_token': request.session['token'],
                               # QUESTION MCJ: Why is this defaulted to v2?
                               'api_ver': request.session.get('api_ver', Versions.DEFAULT_API_VERSION)})
    else:
        return render(request, HOME_PAGE, context={'session_token': None})

############################################################
# BASE TESTS
############################################################
# These tests are version-agnostic for versions 1, 2, and 3.
# The version is passed as a parameter for testing purposes.
# In the event that v3 or future versions break these, we can
# either parameterize the tests further, or

###############
# authorize_link


def _authorize_link(request: HttpRequest, version=Versions.NOT_AN_API_VERSION):
    request.session.update(test_setup(version=version))
    oas = _get_oauth2_session_with_redirect(request)

    authorization_url = oas.authorization_url(
        request.session['authorization_uri'],
        request.session['state'],
        code_challenge=request.session['code_challenge'],
        code_challenge_method=request.session['code_challenge_method']
    )[0]

    return render(
        request,
        'authorize.html',
        {'authorization_url': authorization_url, 'api_ver': version}
    )

###############
# test_coverage


def _test_coverage(request: HttpRequest, version=Versions.NOT_AN_API_VERSION):
    if 'token' not in request.session:
        return redirect('test_links', permanent=True)

    params = [request.session['resource_uri'], version]
    coverage = _get_data_json(request, 'coverage', params)

    nav_info, last_link = extract_page_nav(coverage)

    pg_info = _pagination_info(request, last_link) if nav_info and len(nav_info) > 0 else None

    match version:
        case Versions.V1:
            url_name = 'test_coverage'
        case Versions.V2:
            url_name = 'test_coverage_v2'
        case Versions.V3:
            url_name = 'test_coverage_v3'
            raise
        case _:
            # TODO raise a better error
            raise

    # QUESTION MCJ: Why do we indent an odd number? Why not 2 or 4?
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
    if 'token' not in request.session:
        return redirect('test_links', permanent=True)

    params = [request.session['resource_uri'], version]

    eob = _get_data_json(request, 'eob', params)

    nav_info, last_link = extract_page_nav(eob)

    pg_info = _pagination_info(request, last_link) if nav_info and len(nav_info) > 0 else None

    return render(request, RESULTS_PAGE,
                  {'fhir_json_pretty': json.dumps(eob, indent=3),
                   'url_name': 'test_eob_v2' if version == 2 else 'test_eob',
                   'nav_list': nav_info, 'page_loc': pg_info,
                   'response_type': 'Bundle of ExplanationOfBenefit',
                   'api_ver': 'v2' if version == 2 else 'v1'})

###############
# test_metadata


def _test_metadata(request: HttpRequest, version=Versions.NOT_AN_API_VERSION):
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
            # TODO FIXME
            raise
    json_response = _convert_response_string_to_json(conformance(request))
    return render(request, RESULTS_PAGE,
                  {'fhir_json_pretty': json.dumps(json_response, indent=3),
                   'response_type': 'FHIR Metadata',
                   'api_ver': version
                   })
###############
# test_openid_config


def _test_openid_config(request: HttpRequest, version=Versions.NOT_AN_API_VERSION):
    # api ver agnostic for now, but show version any way on page
    json_response = _convert_response_string_to_json(openid_configuration(request))
    return render(request, RESULTS_PAGE,
                  {'fhir_json_pretty': json.dumps(json_response, indent=3),
                   'response_type': 'OIDC Discovery',
                   'api_ver': 'v2' if v2 else 'v1'})

###############
# test_patient


def _test_patient(request: HttpRequest, version=Versions.NOT_AN_API_VERSION):

    if 'token' not in request.session:
        return redirect('test_links', permanent=True)

    params = [request.session['resource_uri'], 'v1' if version == 1 else 'v2', request.session['patient']]

    patient = _get_data_json(request, 'patient', params)

    return render(request, RESULTS_PAGE,
                  {'fhir_json_pretty': json.dumps(patient, indent=3),
                   'response_type': 'Patient',
                   'api_ver': 'v2' if version == 2 else 'v1'})

###############
# test_userinfo


def _test_userinfo(request: HttpRequest, version=Versions.NOT_AN_API_VERSION):

    if 'token' not in request.session:
        return redirect('test_links', permanent=True)

    params = [request.session['resource_uri'], 'v1' if version == 1 else 'v2']

    user_info = _get_data_json(request, 'userinfo', params)

    return render(request, RESULTS_PAGE,
                  {'fhir_json_pretty': json.dumps(user_info, indent=3),
                   'response_type': 'Profile (OIDC Userinfo)',
                   'api_ver': 'v2' if version == 2 else 'v1'})


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
