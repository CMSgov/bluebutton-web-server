import json
import logging
import math

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from ipware import get_client_ip
from oauthlib.oauth2.rfc6749.errors import MissingTokenError
from oauth2_provider.models import get_application_model
from requests_oauthlib import OAuth2Session
from rest_framework import status
from waffle.decorators import waffle_switch

from .utils import test_setup, get_client_secret, get_app_info_by_id
from apps.dot_ext.loggers import cleanup_session_auth_flow_trace
from apps.fhir.bluebutton.views.home import fhir_conformance, fhir_conformance_v2
from apps.wellknown.views.openid import openid_configuration

import apps.logging.request_logger as bb2logging


Application = get_application_model()

logger = logging.getLogger(bb2logging.HHS_SERVER_LOGNAME_FMT.format(__name__))

HOME_PAGE = "home.html"
HOME2_PAGE = "home2.html"
CLINIC_PAGE = "3rd_party_sample_app.html"
AUTH_PAGE = "authorize2.html"
RESULTS_PAGE = "results.html"
MYAPP_ROOT_PATH = "/myapp/"
APP3RD_ROOT_PATH = "/3rdapp/"
TESTCLIENT_ROOT_PATH = "/testclient/"

# hacky app token registry
# path -> ip -> app : token
CLIENT2TOKEN_MAP = {
    TESTCLIENT_ROOT_PATH: {},
    MYAPP_ROOT_PATH: {},
    APP3RD_ROOT_PATH: {}
}

ENDPOINT_URL_FMT = {
    "userinfo": "{}/{}/connect/userinfo",
    "patient": "{}/{}/fhir/Patient/{}?_format=json",
    "eob": "{}/{}/fhir/ExplanationOfBenefit/?_format=json",
    "coverage": "{}/{}/fhir/Coverage/?_format=json",
}


NAV_URI_FMT = "{}&_count={}&startIndex={}&{}={}"


def _get_page_loc(request, fhir_json):
    total = fhir_json.get('total', 0)
    index = int(request.GET.get('startIndex', 0))
    count = int(request.GET.get('_count', 10))
    return "{}/{}".format(index // count + 1, math.ceil(total / count))


def _extract_page_nav(request, fhir_json):
    link = fhir_json.get('link', None)
    nav_list = []
    if link is not None:
        for lnk in link:
            if lnk.get('url', None) is not None and lnk.get('relation', None) is not None:
                nav_list.append({'relation': lnk['relation'], 'nav_link': lnk['url']})
            else:
                nav_list = []
                break
    return nav_list


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

    return oas.get(uri).json()


def _convert_to_json(json_response):
    return json.loads(json_response.content) if json_response.status_code == 200 else {"error": json_response.status_code}


def _get_oauth2_session_with_token(request):
    return OAuth2Session(
        request.session['client_id'], token=request.session['token'])


def _get_oauth2_session_with_redirect(request):
    return OAuth2Session(request.session['client_id'], redirect_uri=request.session['redirect_uri'])


@waffle_switch('enable_testclient')
def launch3rdapp(request):
    # 3rd party app launched from SBX account, assume every launch is a fresh session
    if 'token' in request.session:
        del request.session['token']

    client_id = None
    client_secret = None

    for key in request.POST:
        if key.startswith('id-3rdapp-'):
            client_id = request.POST[key]
        elif key.startswith('secret-3rdapp-'):
            client_secret = request.POST[key]

    if client_secret and client_id:
        return render(request, CLINIC_PAGE, context={"client_id": client_id, "client_secret": client_secret})
    else:
        return JsonResponse({"error": "Invalid app launch: missing app credential"},
                            status=status.HTTP_400_BAD_REQUEST)


@waffle_switch('enable_testclient')
def restart(request):
    # restart link clicked on API try out page
    if 'token' in request.session:
        del request.session['token']

    return render(request, AUTH_PAGE if request.path.startswith(MYAPP_ROOT_PATH) else HOME_PAGE, context={"session_token": None})


@waffle_switch('enable_testclient')
def callback(request):
    # Authorization has been denied or another error has occured, remove token if existing
    # and redirect to home page view to force re-authorization
    app_name = request.session.get('auth_app_name')
    app_dag_type = request.session.get('auth_app_data_access_type')
    app_pkce_method = request.session.get('auth_pkce_method')
    app_req_demo = request.session.get('auth_require_demographic_scopes')

    if 'error' in request.GET:
        if 'token' in request.session:
            del request.session['token']
            if request.path == MYAPP_ROOT_PATH:
                return redirect(MYAPP_ROOT_PATH, permanent=True)
            else:
                return redirect(TESTCLIENT_ROOT_PATH, permanent=True)

    oas = _get_oauth2_session_with_redirect(request)

    host = settings.HOSTNAME_URL

    if not (host.startswith("http://") or host.startswith("https://")):
        host = "https://%s" % (host)

    auth_uri = host + request.get_full_path()
    token_uri = host
    token_uri += reverse('oauth2_provider_v2:token-v2') \
        if request.session.get('api_ver', 'v1') == 'v2' else reverse('oauth2_provider:token')

    secret = None
    # need client secret here
    if app_name:
        secret = get_client_secret(app_name)

    if secret is None:
        cid = request.session.get('client_id')
        if cid:
            app_name, app_dag_type, app_req_demo, secret = get_app_info_by_id(cid)
            request.session['auth_app_name'] = app_name
            request.session['auth_app_data_access_type'] = app_dag_type
            request.session['auth_require_demographic_scopes'] = app_req_demo

    if secret is None:
        raise Exception("Invalid state: missing info to get access token...")

    try:
        cv = request.session.get('code_verifier')
        token = oas.fetch_token(token_uri,
                                client_secret=secret,
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
    request.session['auth_app_name'] = app_name
    tk = request.session.get('token')
    if request.path.startswith('/myapp/callback'):
        # authorized myapp, redirect to page where app info and FHIR links are ready
        token = _update_client2token_map(request, MYAPP_ROOT_PATH, app_name, new_token=tk)
        return render(request, HOME2_PAGE,
                      context={
                          "session_token": tk,
                          "api_ver": 'v2',
                          "app_name": app_name,
                          "app_dag_type": app_dag_type,
                          "app_req_demo": app_req_demo,
                          "app_pkce_method": app_pkce_method,
                          "api_ver_ending": 'V2',
                          "api_ver_suffix": '-v2'
                      })
    elif request.path.startswith('/3rdapp/callback'):
        # authorized 3rdapp, redirect to page where clinician see claims e.g.
        token = _update_client2token_map(request, APP3RD_ROOT_PATH, app_name, new_token=tk)
        return redirect(APP3RD_ROOT_PATH, permanent=True)
    elif request.path.startswith('/testclient/callback'):
        # authorized testclient, redirect to page where FHIR links are ready
        token = _update_client2token_map(request, TESTCLIENT_ROOT_PATH, app_name, new_token=tk)
        return redirect(TESTCLIENT_ROOT_PATH, permanent=True)
    else:
        return JsonResponse({"error": "Invalid callback path: {}".format(request.path)},
                            status=status.HTTP_400_BAD_REQUEST)


@waffle_switch('enable_testclient')
def authorize(request, **kwargs):
    if request.method == 'POST':
        if request.path.startswith(MYAPP_ROOT_PATH):
            # POST /myapp (default to en locale): parse form for client creds, and
            # generate authorization URL and redirect to medicare login
            client_id = request.POST.get('client_id')
            client_secret = request.POST.get('client_secret')
            if (client_id is not None and client_id.strip() != ""
                    and client_secret is not None and client_secret.strip() != ""):
                app = None
                try:
                    app = Application.objects.get(client_id=client_id)
                except Application.DoesNotExist:
                    pass
                if app:
                    # validate
                    if app.name == 'TestApp':
                        # Also consider exclude other internal apps: e.g. newrelic
                        return JsonResponse({"error": "Not Authorized."},
                                            status=status.HTTP_401_UNAUTHORIZED)
                    if (client_secret == app.client_secret_plain):
                        # generate auth url and redirect
                        request.session.update(test_setup(v2=True, pkce='true', client_id=client_id, path=request.path))
                        request.session['auth_app_name'] = app.name
                        request.session['auth_app_data_access_type'] = app.data_access_type
                        request.session['auth_require_demographic_scopes'] = app.require_demographic_scopes
                        auth_url = _generate_auth_url(request, True)
                        return redirect(auth_url)
                    else:
                        return JsonResponse({"error": "No app found matching the info provided."},
                                            status=status.HTTP_404_NOT_FOUND)
                else:
                    return JsonResponse({"error": "No app found matching the info provided."},
                                        status=status.HTTP_404_NOT_FOUND)
            else:
                return JsonResponse({"error": "Both client_id, and client_secret required."},
                                    status=status.HTTP_400_BAD_REQUEST)
        elif request.path.startswith(APP3RD_ROOT_PATH):
            # POST /3rdapp/ (default to en locale): parse form for client creds, and
            # generate authorization URL and redirect to medicare login
            client_id = request.POST.get('client_id')
            client_secret = request.POST.get('client_secret')
            if (client_id is not None and client_id.strip() != ""
                    and client_secret is not None and client_secret.strip() != ""):
                app = None
                try:
                    app = Application.objects.get(client_id=client_id)
                except Application.DoesNotExist:
                    pass
                if app:
                    # validate
                    if app.name == 'TestApp':
                        # Also consider exclude other internal apps: e.g. newrelic
                        return JsonResponse({"error": "Not Authorized."},
                                            status=status.HTTP_401_UNAUTHORIZED)
                    if (client_secret == app.client_secret_plain):
                        # generate auth url and redirect
                        request.session.update(test_setup(v2=True, pkce='true', client_id=client_id, path=request.path))
                        auth_url = _generate_auth_url(request, True)
                        return redirect(auth_url)
                    else:
                        return JsonResponse({"error": "No app found matching the info provided."},
                                            status=status.HTTP_404_NOT_FOUND)
                else:
                    return JsonResponse({"error": "No app found matching the info provided."},
                                        status=status.HTTP_404_NOT_FOUND)
            else:
                return JsonResponse({"error": "Both client_id, and client_secret required."},
                                    status=status.HTTP_400_BAD_REQUEST)
        else:
            # a bad request, just return json for POC
            # testclient path does not accept POST
            return JsonResponse({"error": "Unexpected request method: {}, path: {}".format(request.method, request.path)},
                                status=status.HTTP_400_BAD_REQUEST)


# New home page view consolidates separate success, error, and access denied views
@waffle_switch('enable_testclient')
def test_links(request, **kwargs):
    if request.method == 'GET':
        # If authorization was successful, pass token to template
        tk = request.session.get('token', None)
        if tk:
            # check path:
            # GET /myapp: load the MyApp authorization page
            # otherwise, load the testclient landing page (the page with 4 authorize buttons)
            # need to check the app name associated with the token
            app_name = request.session.get('auth_app_name')
            if request.path == MYAPP_ROOT_PATH:
                token = _update_client2token_map(request, MYAPP_ROOT_PATH, app_name)
                if token and token['access_token'] == tk['access_token']:
                    # token found, render data
                    app_name = request.session.get('auth_app_name')
                    app_dag_type = request.session.get('auth_app_data_access_type')
                    app_pkce_method = request.session.get('auth_pkce_method')
                    app_req_demo = request.session.get('auth_require_demographic_scopes')
                    return render(request, HOME2_PAGE,
                                  context={"session_token": tk,
                                           "api_ver": 'v2',
                                           "app_name": app_name,
                                           "app_dag_type": app_dag_type,
                                           "app_req_demo": app_req_demo,
                                           "app_pkce_method": app_pkce_method})
                else:
                    # token is for other apps, show AUTH_PAGE
                    return render(request, AUTH_PAGE, context={})
            elif request.path == APP3RD_ROOT_PATH:
                token = _update_client2token_map(request, APP3RD_ROOT_PATH, app_name)
                if token and token['access_token'] == tk['access_token']:
                    # token found fetch claims
                    eob = _get_data_json(request, 'eob', [request.session['resource_uri'], 'v2'])
                    # extract claims from eob (bundle of eob resources)
                    claims = _extract_claims(eob)
                    return render(request, CLINIC_PAGE,
                                  context={'claims': claims})
                else:
                    return render(request, CLINIC_PAGE,
                                  context={})
            else:
                token = _update_client2token_map(request, TESTCLIENT_ROOT_PATH, 'TestApp')
                if token and token['access_token'] == tk['access_token']:
                    # show data end points page
                    ver = request.session.get('api_ver', 'v1')
                    return render(request, HOME_PAGE,
                                  context={"session_token": tk,
                                           "api_ver": ver,
                                           "api_ver_ending": "V2" if ver == 'v2' else "",
                                           "api_ver_suffix": "-v2" if ver == 'v2' else ""}
                                  )
                else:
                    # show the 4 buttons page
                    return render(request, HOME_PAGE, context={"session_token": None})
        else:
            # fresh home or auth page, there is no token
            if request.path == MYAPP_ROOT_PATH:
                return render(request, AUTH_PAGE, context={})
            elif request.path == APP3RD_ROOT_PATH:
                return render(request, CLINIC_PAGE, context={})
            elif request.path == TESTCLIENT_ROOT_PATH:
                return render(request, HOME_PAGE, context={"session_token": None})
            else:
                return JsonResponse({"error": "Invalid path: {}".format(request.path)},
                                    status=status.HTTP_400_BAD_REQUEST)
    else:
        # a bad request, only GET accepted, just return json for POC
        return JsonResponse({"error": "Unexpected method: {}".format(request.method)},
                            status=status.HTTP_400_BAD_REQUEST)


# helper: register the app : token pair under path -> ip context
def _update_client2token_map(request, root, app_name, new_token=None):
    if app_name is None:
        raise Exception("App name required.")
    tk = None
    ip, _ = get_client_ip(request)

    if CLIENT2TOKEN_MAP.get(root).get(ip) is None:
        CLIENT2TOKEN_MAP.get(root)[ip] = {}

    app2token = CLIENT2TOKEN_MAP.get(root)[ip]

    tk = app2token.get(app_name)

    if new_token:
        app2token[app_name] = new_token
    return tk


@never_cache
@waffle_switch('enable_testclient')
def test_userinfo_v2(request):
    return test_userinfo(request, 2)


@never_cache
@waffle_switch('enable_testclient')
def test_userinfo(request, version=1):

    if 'token' not in request.session:
        if request.path == MYAPP_ROOT_PATH:
            return redirect(MYAPP_ROOT_PATH, permanent=True)
        else:
            return redirect(TESTCLIENT_ROOT_PATH, permanent=True)

    params = [request.session['resource_uri'], 'v1' if version == 1 else 'v2']

    user_info = _get_data_json(request, 'userinfo', params)

    return render(request, RESULTS_PAGE,
                  {"fhir_json_pretty": json.dumps(user_info, indent=3),
                   "response_type": "Profile (OIDC Userinfo)",
                   "api_ver": "v2" if version == 2 else "v1"})


@never_cache
@waffle_switch('enable_testclient')
def test_metadata_v2(request):
    return test_metadata(request, True)


@never_cache
@waffle_switch('enable_testclient')
def test_metadata(request, v2=False):
    json_response = _convert_to_json(fhir_conformance_v2(request) if v2 else fhir_conformance(request))
    return render(request, RESULTS_PAGE,
                  {"fhir_json_pretty": json.dumps(json_response, indent=3),
                   "response_type": "FHIR Metadata",
                   "api_ver": "v2" if v2 else "v1",
                   "api_ver_ending": "V2" if v2 else "",
                   "api_ver_suffix": "-v2" if v2 else ""})


@never_cache
@waffle_switch('enable_testclient')
def test_openid_config_v2(request):
    return test_openid_config(request, True)


@never_cache
@waffle_switch('enable_testclient')
def test_openid_config(request, v2=False):
    # api ver agnostic for now, but show version any way on page
    json_response = _convert_to_json(openid_configuration(request))
    return render(request, RESULTS_PAGE,
                  {"fhir_json_pretty": json.dumps(json_response, indent=3),
                   "response_type": "OIDC Discovery",
                   "api_ver": "v2" if v2 else "v1",
                   "api_ver_ending": "V2" if v2 else "",
                   "api_ver_suffix": "-v2" if v2 else ""})


@never_cache
@waffle_switch('enable_testclient')
def test_coverage_v2(request):
    return test_coverage(request, 2)


@never_cache
@waffle_switch('enable_testclient')
def test_coverage(request, version=1):

    if 'token' not in request.session:
        if request.path == MYAPP_ROOT_PATH:
            return redirect(MYAPP_ROOT_PATH, permanent=True)
        else:
            return redirect(TESTCLIENT_ROOT_PATH, permanent=True)

    coverage = _get_data_json(request, 'coverage', [request.session['resource_uri'], 'v1' if version == 1 else 'v2'])

    nav_info = _extract_page_nav(request, coverage)

    if coverage.get('total', 0) == 0:
        # defensive
        nav_info = []

    return render(request, RESULTS_PAGE,
                  {"fhir_json_pretty": json.dumps(coverage, indent=3),
                   "url_name": 'test_coverage_v2' if version == 2 else 'test_coverage',
                   "nav_list": nav_info, "page_loc": _get_page_loc(request, coverage),
                   "response_type": "Bundle of Coverage",
                   "total_resource": coverage.get('total', 0),
                   "api_ver": "v2" if version == 2 else "v1",
                   "api_ver_ending": "V2" if version == 2 else "",
                   "api_ver_suffix": "-v2" if version == 2 else ""})


@never_cache
@waffle_switch('enable_testclient')
def test_patient_v2(request):
    return test_patient(request, 2)


@never_cache
@waffle_switch('enable_testclient')
def test_patient(request, version=1):

    if 'token' not in request.session:
        if request.path == MYAPP_ROOT_PATH:
            return redirect(MYAPP_ROOT_PATH, permanent=True)
        else:
            return redirect(TESTCLIENT_ROOT_PATH, permanent=True)

    params = [request.session['resource_uri'], 'v1' if version == 1 else 'v2', request.session['patient']]

    patient = _get_data_json(request, 'patient', params)
    # result page only use api_ver, other context provided anyways
    return render(request, RESULTS_PAGE,
                  {"fhir_json_pretty": json.dumps(patient, indent=3),
                   "response_type": "Patient",
                   "api_ver": "v2" if version == 2 else "v1",
                   "api_ver_ending": "V2" if version == 2 else "",
                   "api_ver_suffix": "-v2" if version == 2 else ""})


@never_cache
@waffle_switch('enable_testclient')
def test_eob_v2(request):
    return test_eob(request, 2)


@never_cache
@waffle_switch('enable_testclient')
def test_eob(request, version=1):
    if 'token' not in request.session:
        if request.path == MYAPP_ROOT_PATH:
            return redirect(MYAPP_ROOT_PATH, permanent=True)
        else:
            return redirect(TESTCLIENT_ROOT_PATH, permanent=True)

    params = [request.session['resource_uri'], 'v1' if version == 1 else 'v2']

    eob = _get_data_json(request, 'eob', params)

    nav_info = _extract_page_nav(request, eob)

    if eob.get('total', 0) == 0:
        # defensive
        nav_info = []

    return render(request, RESULTS_PAGE,
                  {"fhir_json_pretty": json.dumps(eob, indent=3),
                   "url_name": 'test_eob_v2' if version == 2 else 'test_eob',
                   "nav_list": nav_info, "page_loc": _get_page_loc(request, eob),
                   "response_type": "Bundle of ExplanationOfBenefit",
                   "total_resource": eob.get('total', 0),
                   "api_ver": "v2" if version == 2 else "v1",
                   "api_ver_ending": "V2" if version == 2 else "",
                   "api_ver_suffix": "-v2" if version == 2 else ""})


@never_cache
@waffle_switch('enable_testclient')
def authorize_link_v2(request):
    return authorize_link(request, True)


@never_cache
@waffle_switch('enable_testclient')
def authorize_link(request, v2=False):
    pkce_enabled = request.GET.get('pkce')
    request.session.update(test_setup(v2=v2, pkce=pkce_enabled, path=request.path))
    authorization_url = _generate_auth_url(request, pkce_enabled)
    if request.path.startswith('/myapp/authorize-link-v2'):
        return render(request, 'authorize2.html', {})
    else:
        return render(request, 'authorize.html',
                      {"authorization_url": authorization_url, "api_ver": "v2" if v2 else "v1"})


def _generate_auth_url(request, pkce_enabled):
    oas = _get_oauth2_session_with_redirect(request)
    authorization_url = None
    if pkce_enabled:
        authorization_url = oas.authorization_url(
            request.session['authorization_uri'],
            request.session['state'],
            code_challenge=request.session['code_challenge'],
            code_challenge_method=request.session['code_challenge_method'])[0]
    else:
        authorization_url = oas.authorization_url(
            request.session['authorization_uri'])[0]
    return authorization_url


# POC: extract claims as list of tuples (code, drug name, cost)
# refer to sample app ts logic for extracting claims:
# code: resource.item[0]?.productOrService?.coding[0]?.code || 'Unknown',
# display: resource.item[0]?.productOrService?.coding[0]?.display || 'Unknown Prescription Drug',
# amount: resource.item[0]?.adjudication[7]?.amount?.value || '0'
def _extract_claims(eob):
    claims = []
    if eob and eob.get('entry'):
        for r in eob['entry']:
            items = r['resource']['item']
            # only sampling element 0 for demo purpose
            if items and items[0]:
                prod_and_service = items[0]['productOrService']
                adjudications = items[0]['adjudication']
                if prod_and_service and adjudications:
                    claim = {'code': 'Unknown', 'name': 'Unknown Prescription Drug', 'cost': '0'}
                    coding = prod_and_service['coding']
                    if coding and coding[0]:
                        claim['code'] = coding[0].get('code', 'Unknown')
                        claim['name'] = coding[0].get('display', 'Unknown Prescription Drug')
                    if adjudications and len(adjudications) >= 7:
                        if adjudications[7].get('amount', None):
                            amt = adjudications[7].get('amount')
                            if amt:
                                claim['cost'] = "{} {}".format(amt.get('value', '0'), amt.get('currency', ''))

                    claims.append(claim)
    else:
        raise Exception("Bad claims data..., expecting EOBs but got: {}".format(eob))
    return claims
