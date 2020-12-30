from django.shortcuts import render, redirect
from requests_oauthlib import OAuth2Session
from collections import OrderedDict
from django.http import JsonResponse
from django.conf import settings
from django.urls import reverse
from .utils import test_setup, get_client_secret
import logging
from oauthlib.oauth2.rfc6749.errors import MissingTokenError
from django.views.decorators.cache import never_cache
from apps.dot_ext.loggers import cleanup_session_auth_flow_trace

logger = logging.getLogger('hhs_server.%s' % __name__)


def callback(request):
    # Authorization has been denied or another error has occured, remove token if existing
    # and redirect to home page view to force re-authorization
    if 'error' in request.GET:
        if 'token' in request.session:
            del request.session['token']
        return redirect('test_links', permanent=True)

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


# Set up ability to determine if user has token
def test_links(request):
    if 'token' in request.session:
        session_has_token = True
    else:
        session_has_token = False
    return render(request, 'testlinks.html', context={"session_has_token": session_has_token})


@never_cache
def test_userinfo(request):
    if 'token' not in request.session:
        return redirect('test_links', permanent=True)
    oas = OAuth2Session(
        request.session['client_id'], token=request.session['token'])
    userinfo_uri = "%s/v1/connect/userinfo" % (request.session['resource_uri'])
    userinfo = oas.get(userinfo_uri).json()
    return JsonResponse(userinfo)


@never_cache
def test_coverage(request):
    if 'token' not in request.session:
        return redirect('test_links', permanent=True)
    oas = OAuth2Session(
        request.session['client_id'], token=request.session['token'])
    coverage_uri = "%s/v1/fhir/Coverage/?_format=json" % (
        request.session['resource_uri'])

    coverage = oas.get(coverage_uri).json()
    return JsonResponse(coverage, safe=False)


@never_cache
def test_patient(request):
    if 'token' not in request.session:
        return redirect('test_links', permanent=True)
    oas = OAuth2Session(
        request.session['client_id'], token=request.session['token'])
    patient_uri = "%s/v1/fhir/Patient/%s?_format=json" % (
        request.session['resource_uri'], request.session['patient'])
    patient = oas.get(patient_uri).json()
    return JsonResponse(patient)


@never_cache
def test_eob(request):
    if 'token' not in request.session:
        return redirect('test_links', permanent=True)
    oas = OAuth2Session(
        request.session['client_id'], token=request.session['token'])
    eob_uri = "%s/v1/fhir/ExplanationOfBenefit/?_format=json" % (
        request.session['resource_uri'])
    eob = oas.get(eob_uri).json()
    return JsonResponse(eob)


def authorize_link(request):
    request.session.update(test_setup())
    oas = OAuth2Session(request.session['client_id'],
                        redirect_uri=request.session['redirect_uri'])
    authorization_url = oas.authorization_url(
        request.session['authorization_uri'])[0]
    return render(request, 'testclient.html', {"authorization_url": authorization_url})
