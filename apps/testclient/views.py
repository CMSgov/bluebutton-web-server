from __future__ import absolute_import
from __future__ import unicode_literals
from django.shortcuts import render
from requests_oauthlib import OAuth2Session
from collections import OrderedDict
from django.http import JsonResponse
from django.conf import settings
from django.core.urlresolvers import reverse
from .utils import test_setup

__author__ = "Alan Viars"


def callback(request):

    response = OrderedDict()

    oas = OAuth2Session(request.session['client_id'],
                        redirect_uri=request.session['redirect_uri'])
    auth_uri = settings.HOSTNAME_URL + request.get_full_path()
    token = oas.fetch_token(request.session['token_uri'],
                            client_secret=request.session['client_secret'],
                            authorization_response=auth_ur)
    request.session['token'] = token
    response['token_response'] = OrderedDict()

    for k, v in token.items():
        if k != "scope":
            response['token_response'][k] = v
        else:
            response['token_response'][k] = ' '.join(v)

    userinfo = oas.get(request.session['userinfo_uri']).json()
    response[request.session['userinfo_uri']] = userinfo
    request.session['patient'] = userinfo['patient']

    response['oidc_discovery_uri'] = settings.HOSTNAME_URL + \
        reverse('openid-configuration')

    response['fhir_metadata_uri'] = settings.HOSTNAME_URL + \
        '/protected/bluebutton/fhir/v1/metadata'

    response['test_page'] = settings.HOSTNAME_URL + reverse('test_links')

    return JsonResponse(response)


def test_userinfo(request):
    oas = OAuth2Session(
        request.session['client_id'], token=request.session['token'])
    userinfo_uri = "%s/connect/userinfo" % (request.session['resource_uri'])
    userinfo = oas.get(userinfo_uri).json()
    return JsonResponse(userinfo)


def test_coverage(request):
    oas = OAuth2Session(
        request.session['client_id'], token=request.session['token'])
    coverage_uri = "%s/protected/bluebutton/fhir/v1/Coverage/?_format=json" % (
        request.session['resource_uri'])

    coverage = oas.get(coverage_uri).json()
    return JsonResponse(coverage, safe=False)


def test_patient(request):
    oas = OAuth2Session(
        request.session['client_id'], token=request.session['token'])
    patient_uri = "%s/protected/bluebutton/fhir/v1/Patient/%s?_format=json" % (
        request.session['resource_uri'], request.session['patient'])
    patient = oas.get(patient_uri).json()
    return JsonResponse(patient)


def test_eob(request):
    oas = OAuth2Session(
        request.session['client_id'], token=request.session['token'])
    eob_uri = "%s/protected/bluebutton/fhir/v1/ExplanationOfBenefit/?patient=%s&_format=json" % (
        request.session['resource_uri'], request.session['patient'])
    eob = oas.get(eob_uri).json()
    return JsonResponse(eob)


def authorize_link(request):

    request.session.update(test_setup())
    oas = OAuth2Session(request.session['client_id'],
                        redirect_uri=request.session['redirect_uri'])
    authorization_url = oas.authorization_url(
        request.session['authorization_uri'])[0]
    return render(request, 'testclient.html', {"authorization_url": authorization_url})


def test_links(request):
    return render(request, 'testlinks.html')
