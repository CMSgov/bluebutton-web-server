import json
import logging

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from oauthlib.oauth2.rfc6749.errors import MissingTokenError
from requests_oauthlib import OAuth2Session
from rest_framework import status
from urllib.parse import parse_qs, urlparse

from waffle.decorators import waffle_switch

from .utils import test_setup, get_client_secret, extract_page_nav
from apps.dot_ext.loggers import cleanup_session_auth_flow_trace
from apps.fhir.bluebutton.views.home import fhir_conformance
from apps.wellknown.views.openid import openid_configuration

import apps.logging.request_logger as bb2logging

logger = logging.getLogger(bb2logging.HHS_SERVER_LOGNAME_FMT.format(__name__))

HOME_PAGE = "home.html"
RESULTS_PAGE = "results.html"

ENDPOINT_URL_FMT = {
    "userinfo": "{}/{}/connect/userinfo",
    "patient": "{}/{}/fhir/Patient/{}?_format=json",
    "eob": "{}/{}/fhir/ExplanationOfBenefit/?_format=json",
    "coverage": "{}/{}/fhir/Coverage/?_format=json",
}


NAV_URI_FMT = "{}&_count={}&startIndex={}&{}={}"


def _get_data_json(request, name, params):

    oas = _get_oauth2_session_with_token(request)

    nav_link = request.GET.get('nav_link', None)

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

    r = oas.get(uri)
    return r.json()


def _convert_to_json(json_response):
    return json.loads(json_response.content) if json_response.status_code == 200 else {"error": json_response.status_code}


def _get_oauth2_session_with_token(request):
    return OAuth2Session(
        request.session['client_id'], token=request.session['token'])


def _get_oauth2_session_with_redirect(request):
    return OAuth2Session(
        request.session['client_id'], redirect_uri=request.session['redirect_uri'])


@waffle_switch('enable_testclient')
def restart(request):
    # restart link clicked on API try out page
    if 'token' in request.session:
        del request.session['token']

    return render(request, HOME_PAGE, context={"session_token": None})


@waffle_switch('enable_testclient')
def callback(request):
    # Authorization has been denied or another error has occured, remove token if existing
    # and redirect to home page view to force re-authorization
    if 'error' in request.GET:
        if 'token' in request.session:
            del request.session['token']
        return redirect('test_links', permanent=True)

    oas = _get_oauth2_session_with_redirect(request)

    host = settings.HOSTNAME_URL

    if not (host.startswith("http://") or host.startswith("https://")):
        host = "https://%s" % (host)

    auth_uri = host + request.get_full_path()
    token_uri = host
    token_uri += reverse('oauth2_provider_v2:token-v2') \
        if request.session.get('api_ver', 'v1') == 'v2' else reverse('oauth2_provider:token')

    try:
        cv = request.session.get('code_verifier')
        token = oas.fetch_token(token_uri,
                                client_secret=get_client_secret(),
                                authorization_response=auth_uri,
                                code_verifier=cv if cv else '')
    except MissingTokenError:
        logmsg = "Failed to get token from %s" % (request.session['token_uri'])
        logger.error(logmsg)
        return JsonResponse({'error': 'Failed to get token from',
                             'code': 'MissingTokenError',
                             'help': 'Try authorizing again.'}, status=500)

    # For test client allow only authorize on synthetic beneficiaries
    patient = token.get("patient", None)
    if patient is not None and not patient.startswith("-"):
        logmsg = "Failed token is for a non-synthetic patient ID = %s" % (token.get("patient", ""))
        logger.error(logmsg)
        if 'token' in request.session:
            del request.session['token']
        return JsonResponse({'error': logmsg,
                             'code': 'NonSyntheticTokenError',
                             'help': 'Try authorizing again.'}, status=status.HTTP_403_FORBIDDEN)

    request.session['token'] = token

    userinfo_uri = request.session['userinfo_uri']
    try:
        userinfo = oas.get(userinfo_uri).json()
    except Exception:
        userinfo = {'patient': token.get('patient', None)}

    request.session['patient'] = userinfo.get('patient', token.get('patient', None))

    # We are done using auth flow trace, clear from the session.
    cleanup_session_auth_flow_trace(request)

    # Successful token response, redirect to home page view
    return redirect('test_links', permanent=True)


# New home page view consolidates separate success, error, and access denied views
@waffle_switch('enable_testclient')
def test_links(request, **kwargs):
    # If authorization was successful, pass token to template
    if 'token' in request.session:
        return render(request, HOME_PAGE,
                      context={"session_token": request.session['token'],
                               "api_ver": request.session.get('api_ver', 'v2')})
    else:
        return render(request, HOME_PAGE, context={"session_token": None})


# userinfo v3 currently not returning anything so this one is broken
@never_cache
@waffle_switch('enable_testclient')
def test_userinfo_v3(request):
    return test_userinfo(request, ver='v3')


@never_cache
@waffle_switch('enable_testclient')
def test_userinfo_v2(request):
    return test_userinfo(request, ver='v2')


@never_cache
@waffle_switch('enable_testclient')
def test_userinfo(request, ver='v1'):

    if 'token' not in request.session:
        return redirect('test_links', permanent=True)

    params = [request.session['resource_uri'], ver]

    user_info = _get_data_json(request, 'userinfo', params)

    return render(request, RESULTS_PAGE,
                  {"fhir_json_pretty": json.dumps(user_info, indent=3),
                   "response_type": "Profile (OIDC Userinfo)",
                   "api_ver": ver})


@never_cache
@waffle_switch('enable_testclient')
def test_metadata_v3(request):
    return test_metadata(request, ver='v3')


@never_cache
@waffle_switch('enable_testclient')
def test_metadata_v2(request):
    return test_metadata(request, ver='v2')


@never_cache
@waffle_switch('enable_testclient')
def test_metadata(request, ver='v1'):
    json_response = _convert_to_json(fhir_conformance(request, ver_str=ver))
    return render(request, RESULTS_PAGE,
                  {"fhir_json_pretty": json.dumps(json_response, indent=3),
                   "response_type": "FHIR Metadata",
                   "api_ver": ver})


# This is still using /.well-known/openid-configuration-v2, so not the most accurate for v3
@never_cache
@waffle_switch('enable_testclient')
def test_openid_config_v3(request):
    return test_openid_config(request, ver='v3')


@never_cache
@waffle_switch('enable_testclient')
def test_openid_config_v2(request):
    return test_openid_config(request, ver='v2')


@never_cache
@waffle_switch('enable_testclient')
def test_openid_config(request, ver='v1'):
    # api ver agnostic for now, but show version any way on page
    json_response = _convert_to_json(openid_configuration(request))
    return render(request, RESULTS_PAGE,
                  {"fhir_json_pretty": json.dumps(json_response, indent=3),
                   "response_type": "OIDC Discovery",
                   "api_ver": ver})


@never_cache
@waffle_switch('enable_testclient')
def test_coverage_v3(request):
    return test_coverage(request, ver='v3', url_name='test_coverage_v3')


@never_cache
@waffle_switch('enable_testclient')
def test_coverage_v2(request):
    return test_coverage(request, ver='v2', url_name='test_coverage_v2')


@never_cache
@waffle_switch('enable_testclient')
def test_coverage(request, ver='v1', url_name='test_coverage'):

    if 'token' not in request.session:
        return redirect('test_links', permanent=True)

    coverage = _get_data_json(request, 'coverage', [request.session['resource_uri'], ver])

    nav_info, last_link = extract_page_nav(coverage)

    pg_info = _pagination_info(request, last_link) if nav_info and len(nav_info) > 0 else None

    return render(request, RESULTS_PAGE,
                  {"fhir_json_pretty": json.dumps(coverage, indent=3),
                   "url_name": url_name,
                   "nav_list": nav_info, "page_loc": pg_info,
                   "response_type": "Bundle of Coverage",
                   "api_ver": ver})


@never_cache
@waffle_switch('enable_testclient')
def test_patient_v3(request):
    return test_patient(request, ver='v3')


@never_cache
@waffle_switch('enable_testclient')
def test_patient_v2(request):
    return test_patient(request, ver='v2')


@never_cache
@waffle_switch('enable_testclient')
def test_patient(request, ver='v1'):

    if 'token' not in request.session:
        return redirect('test_links', permanent=True)

    params = [request.session['resource_uri'], ver, request.session['patient']]

    patient = _get_data_json(request, 'patient', params)

    return render(request, RESULTS_PAGE,
                  {"fhir_json_pretty": json.dumps(patient, indent=3),
                   "response_type": "Patient",
                   "api_ver": ver})


@never_cache
@waffle_switch('enable_testclient')
def test_eob_v3(request):
    return test_eob(request, ver='v3', url_name='test_eob_v3')


@never_cache
@waffle_switch('enable_testclient')
def test_eob_v2(request):
    return test_eob(request, ver='v2', url_name='test_eob_v2')


@never_cache
@waffle_switch('enable_testclient')
def test_eob(request, ver='v1', url_name='test_eob'):
    if 'token' not in request.session:
        return redirect('test_links', permanent=True)

    params = [request.session['resource_uri'], ver]

    eob = _get_data_json(request, 'eob', params)

    nav_info, last_link = extract_page_nav(eob)

    pg_info = _pagination_info(request, last_link) if nav_info and len(nav_info) > 0 else None

    return render(request, RESULTS_PAGE,
                  {"fhir_json_pretty": json.dumps(eob, indent=3),
                   "url_name": url_name,
                   "nav_list": nav_info, "page_loc": pg_info,
                   "response_type": "Bundle of ExplanationOfBenefit",
                   "api_ver": ver})


@never_cache
@waffle_switch('enable_testclient')
def authorize_link_v3(request):
    return authorize_link(request, ver="v3")


@never_cache
@waffle_switch('enable_testclient')
def authorize_link_v2(request):
    return authorize_link(request, ver="v2")


@never_cache
@waffle_switch('enable_testclient')
def authorize_link(request, ver="v1"):
    request.session.update(test_setup(ver=ver))
    oas = _get_oauth2_session_with_redirect(request)

    oas.scope = "profile openid patient/Patient.rs patient/ExplanationOfBenefit.rs patient/Coverage.rs"

    authorization_url = oas.authorization_url(
        request.session['authorization_uri'],
        request.session['state'],
        code_challenge=request.session['code_challenge'],
        code_challenge_method=request.session['code_challenge_method'],
    )[0]

    return render(
        request,
        'authorize.html',
        {"authorization_url": authorization_url, "api_ver": ver}
    )


def _pagination_info(request, last_url):
    # with no total resource count of a bundle, use
    # backend pagination links for total page vs current page
    cur_start_index = int(request.GET.get('startIndex', 0))
    pg_count = int(request.GET.get('_count', 10))
    qparams = parse_qs(urlparse(last_url).query)
    last_pg_index = qparams.get('startIndex', 0)

    pg_info = "No pagination info from backend"

    if last_pg_index:
        last_pg_index = int(last_pg_index[0])
        pg_info = "{}/{}".format(cur_start_index // pg_count + 1, last_pg_index // pg_count + 1)

    return pg_info
