from django.shortcuts import render
from requests_oauthlib import OAuth2Session
from collections import OrderedDict
from django.http import JsonResponse, HttpResponseRedirect
from django.conf import settings
from django.urls import reverse
from .utils import test_setup, get_client_secret
import logging
from oauthlib.oauth2.rfc6749.errors import MissingTokenError
from django.views.decorators.cache import never_cache
from apps.dot_ext.loggers import cleanup_session_auth_flow_trace

logger = logging.getLogger('hhs_server.%s' % __name__)


@never_cache
def callback(request):
    response = OrderedDict()
    if 'error' in request.GET:
        return render(request, "access-denied.html", {"error": request.GET.get("error")})
    oas = OAuth2Session(request.session['client_id'],
                        redirect_uri=request.session['redirect_uri'])
    host = settings.HOSTNAME_URL
    if not(host.startswith("http://") or host.startswith("https://")):
        host = "https://%s" % (host)
    auth_uri = host + request.get_full_path()
    token_uri = host + reverse('oauth2_provider:token')
    try:
        token = oas.fetch_token(token_uri,
                                client_secret=get_client_secret(),
                                authorization_response=auth_uri)
    except MissingTokenError:
        logmsg = "Failed to get token from %s" % (request.session['token_uri'])
        logger.error(logmsg)
        return JsonResponse({'error': 'Failed to get token from',
                             'code': 'MissingTokenError',
                             'help': 'Try authorizing again.'}, status=500)
    request.session['token'] = token
    response['token_response'] = OrderedDict()

    for k, v in token.items():
        if k != "scope":
            response['token_response'][k] = v
        else:
            response['token_response'][k] = ' '.join(v)
    userinfo_uri = request.session['userinfo_uri']
    try:
        userinfo = oas.get(userinfo_uri).json()
    except Exception:
        userinfo = {'patient': token.get('patient', None)}

    request.session['patient'] = userinfo.get('patient', token.get('patient', None))

    response['userinfo'] = {'patient': request.session.get('patient', None)}

    response['oidc_discovery_uri'] = host + \
        reverse('openid-configuration')

    response['fhir_metadata_uri'] = host + \
        reverse('fhir_conformance_metadata')

    response['test_page'] = host + reverse('test_links')

    # We are done using auth flow trace, clear from the session.
    cleanup_session_auth_flow_trace(request)

    return success(request, response)


@never_cache
def success(request, response):
    return render(request, "success.html", response)


@never_cache
def test_userinfo(request):
    if 'token' not in request.session:
        return HttpResponseRedirect(reverse('testclient_error_page'))
    oas = OAuth2Session(
        request.session['client_id'], token=request.session['token'])
    userinfo = oas.get(
        "{}/v1/connect/userinfo/?_format=json&fhir_ver={}".format(
            request.session['resource_uri'], "v2" if request.path.endswith('userinfoV2') else "v1")).json()
    return JsonResponse(userinfo)


@never_cache
def test_coverage(request):
    return check_token_and_query(request, 'Coverage')


@never_cache
def test_patient(request):
    return check_token_and_query(request, 'Patient')


@never_cache
def test_eob(request):
    return check_token_and_query(request, 'ExplanationOfBenefit')


def authorize_link(request):

    request.session.update(test_setup())
    oas = OAuth2Session(request.session['client_id'],
                        redirect_uri=request.session['redirect_uri'])
    authorization_url = oas.authorization_url(
        request.session['authorization_uri'])[0]
    return render(request, 'testclient.html', {"authorization_url": authorization_url})


def test_links(request):
    return render(request, 'testlinks.html')


@never_cache
def check_token_and_query(request, resource_name):
    '''
    helper: check token in session and add fhir version parameter
    if a BFD v2 request intended
    '''
    if 'token' not in request.session:
        return HttpResponseRedirect(reverse('testclient_error_page'))
    oas = OAuth2Session(
        request.session['client_id'], token=request.session['token'])
    fhir_resource = None
    if request.path.endswith('{}V2'.format(resource_name)):
        # BB2-291: append query parameter fhir_ver=r4
        fhir_resource = oas.get(
            "{}/v1/fhir/{}/?_format=json&fhir_ver=r4".format(
                request.session['resource_uri'], resource_name)).json()
    else:
        fhir_resource = oas.get(
            "{}/v1/fhir/{}/?_format=json".format(
                request.session['resource_uri'], resource_name)).json()
    return JsonResponse(fhir_resource, safe=False)
