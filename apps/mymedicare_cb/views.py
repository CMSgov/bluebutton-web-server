from __future__ import absolute_import
from __future__ import unicode_literals
from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User, Group
from django.contrib.auth import login
import requests
from django.http import HttpResponse
from apps.accounts.models import UserProfile
from apps.fhir.bluebutton.models import Crosswalk
from apps.fhir.bluebutton.utils import get_resourcerouter
import urllib.request as req
import random
from .models import AnonUserState

__author__ = "Alan Viars"


def callback(request):
    token_endpoint = getattr(
        settings, 'SLS_TOKEN_ENDPOINT', 'https://dev.accounts.cms.gov/v1/oauth/token')
    redirect_uri = getattr(settings, 'SLS_REDIRECT_URI',
                           'http://localhost:8000/mymedicare/sls-callback')
    userinfo_endpoint = getattr(
        settings, 'SLS_USERINFO_ENDPOINT', 'https://dev.accounts.cms.gov/v1/oauth/userinfo')
    verify_ssl = getattr(settings, 'SLS_VERIFY_SSL', False)
    code = request.GET.get('code')
    state = request.GET.get('state')
    aus = AnonUserState.objects.get(state=state)
    next_uri = aus.next_uri
    token_dict = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri}

    # Call SLS token api: ", "https://dev.accounts.cms.gov/v1/oauth/token"  as
    # a POST
    r = requests.post(token_endpoint, json=token_dict, verify=verify_ssl)
    token_response = {}
    if r.status_code != 200:
        return HttpResponse("An unknown error has occurred.", status=500)

    token_response = r.json()
    # Create the Bearer
    bt = "Bearer %s" % (token_response['access_token'])
    # build a headers dict with Authorization
    headers = {"Authorization": bt}
    # Call SLS userinfo: ",
    # "https://dev.api.bluebutton.cms.gov/v1/oauth/userinfo  as a GET with
    # Authorization Bearer token in header.
    r = requests.get(userinfo_endpoint, headers=headers, verify=verify_ssl)
    # print("Status", r.status_code)
    if r.status_code != 200:
        return HttpResponse("An unknown error has occurred.", status=500)
    # Get the userinfo response object
    user_info = r.json()
    try:
        user = User.objects.get(username=user_info['sub'])
        if not user.first_name:
            user.first_name = user_info['given_name']
        if not user.last_name:
            user.last_name = user_info['family_name']
        if not user.email:
            user.email = user_info['email']
        user.save()
    except User.DoesNotExist:
        # Create a new user. Note that we can set password
        # to anything, because it won't be checked.
        user = User(username=user_info['sub'], password='',
                    first_name=user_info['given_name'],
                    last_name=user_info['family_name'],
                    email=user_info['email'])
        user.save()
    up, created = UserProfile.objects.get_or_create(
        user=user, user_type='BEN')
    group = Group.objects.get(name='BlueButton')
    user.groups.add(group)
    # Log in the user
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)
    # Determine patient_id
    fhir_source = get_resourcerouter()
    cx, g_o_c = Crosswalk.objects.get_or_create(
        user=user, fhir_source=fhir_source)
    hicn = user_info.get('hicn', "999999999A")
    cx.user_id_hash = hicn
    cx.save()
    # URL for patient ID.
    url = fhir_source.fhir_url + \
        "Patient/?identifier=http%3A%2F%2Fbluebutton.cms.hhs.gov%2Fidentifier%23hicnHash%7C" + \
        cx.user_id_hash + \
        "&_format=json"
    response = requests.get(url, cert=("../certstore/ca.cert.pem", "../certstore/ca.key.nocrypt.pem"),
                            verify=False)

    if 'entry' in response.json():
        identifiers = response.json()['entry'][0]['resource']['identifier']
        fhir_id = ""
        for i in identifiers:
            if i['system'] == 'http://bluebutton.cms.hhs.gov/identifier#bene_id':
                fhir_id = i['value']
            if fhir_id:
                cx.fhir_id = fhir_id
                cx.save()
    # Get first and last naem from FHIR if not in OIDC Userinfo response.
    if user_info['given_name'] == "" or user_info['family_name'] == "":
        if 'entry' in response.json():
            if 'name' in response.json()['entry'][0]['resource']:
                names = response.json()['entry'][0]['resource']['name']
                first_name = ""
                last_name = ""
                for n in names:
                    if n['use'] == 'usual':
                        last_name = n['family']
                        first_name = n['given'][0]
                    if last_name or first_name:
                        user.first_name = first_name
                        user.last_name = last_name
                        user.save()

    # Delete the AUS since its not longer needed or valid:
    aus.delete()
    return HttpResponseRedirect(next_uri)


def generate_nonce(length=26):
    """Generate pseudo-random number."""
    return ''.join([str(random.randint(0, 9)) for i in range(length)])


def mymedicare_login(request):
    mymedicare_login_url = getattr(settings, 'MEDICARE_LOGIN_URI',
                                   'https://dev2.account.mymedicare.gov/?scope=openid%20profile&client_id=bluebutton')
    redirect = getattr(settings, 'MEDICARE_REDIRECT_URI',
                       'http://localhost:8000/mymedicare/sls-callback')
    redirect = req.pathname2url(redirect)
    state = generate_nonce()
    state = req.pathname2url(state)
    mymedicare_login_url = "%s&state=%s&redirect_uri=%s" % (
        mymedicare_login_url, state, redirect)
    # print(mymedicare_login_url)
    next_uri = request.GET.get('next')
    # print("Next URI", next_uri)
    AnonUserState.objects.create(state=state, next_uri=next_uri)
    template_name = getattr(
        settings, 'MEDICARE_LOGIN_TEMPLATE_NAME', "accounts/login.html")
    return render(request, template_name, {'next': next_uri,
                                           'mymedicare_login_url': mymedicare_login_url})
