from __future__ import absolute_import
from __future__ import unicode_literals
from django.conf import settings
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Group
from django.contrib.auth import login
import requests
from django.http import HttpResponse, JsonResponse
from apps.accounts.models import UserProfile
from apps.fhir.bluebutton.models import Crosswalk
from apps.fhir.bluebutton.utils import get_resourcerouter, FhirServerAuth
import urllib.request as req
import random
from .models import AnonUserState
import logging
from django.shortcuts import render
from django.views.decorators.cache import never_cache

__author__ = "Alan Viars"

logger = logging.getLogger('hhs_server.%s' % __name__)


@never_cache
def callback(request):
    token_endpoint = settings.SLS_TOKEN_ENDPOINT
    redirect_uri = settings.MEDICARE_REDIRECT_URI
    userinfo_endpoint = getattr(
        settings, 'SLS_USERINFO_ENDPOINT', 'https://test.accounts.cms.gov/v1/oauth/userinfo')
    verify_ssl = getattr(settings, 'SLS_VERIFY_SSL', False)
    code = request.GET.get('code')
    state = request.GET.get('state')
    try:
        aus = AnonUserState.objects.get(state=state)
    except AnonUserState.DoesNotExist:
        return JsonResponse({"error": "your OAuth2 client application must supply a state code."},
                            status=400)
    next_uri = aus.next_uri
    token_dict = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri}
    logger.debug("token_endpoint %s" % (token_endpoint))
    logger.debug("redirect_uri %s" % (redirect_uri))
    # Call SLS token API
    r = requests.post(token_endpoint, json=token_dict, verify=verify_ssl)
    token_response = {}
    if r.status_code != 200:
        logger.error("Token request response error %s" % (r.status_code))
        return HttpResponse("Error: HTTP %s from the token response." % (r.status_code), status=r.status_code)
    token_response = r.json()
    # Create the Bearer
    bt = "Bearer %s" % (token_response['access_token'])
    # build a headers dict with Authorization
    headers = {"Authorization": bt}
    # Call SLS userinfo: ",
    # Authorization Bearer token in header.
    r = requests.get(userinfo_endpoint, headers=headers, verify=verify_ssl)

    if r.status_code != 200:
        logger.error("User info request response error %s" % (r.status_code))
        return HttpResponse("Error: HTTP %s response from userinfo request." % (r.status_code), status=r.status_code)
    # Get the userinfo response object
    user_info = r.json()
    try:
        user = User.objects.get(username=user_info['sub'][9:36])
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
        user = User(username=user_info['sub'][9:36], password='',
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
    crosswalk, g_o_c = Crosswalk.objects.get_or_create(
        user=user, fhir_source=fhir_source)
    hicn = user_info.get('hicn', "")
    crosswalk.user_id_hash = hicn
    crosswalk.save()
    auth_state = FhirServerAuth(None)
    certs = (auth_state['cert_file'], auth_state['key_file'])

    # URL for patient ID.
    url = fhir_source.fhir_url + \
        "Patient/?identifier=http%3A%2F%2Fbluebutton.cms.hhs.gov%2Fidentifier%23hicnHash%7C" + \
        crosswalk.user_id_hash + \
        "&_format=json"
    response = requests.get(url, cert=certs, verify=False)

    if 'entry' in response.json() and response.json()['total'] == 1:
        fhir_id = response.json()['entry'][0]['resource']['id']
        crosswalk.fhir_id = fhir_id
        crosswalk.save()

    # Get first and last name from FHIR if not in OIDC Userinfo response.
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


@never_cache
def mymedicare_login(request):
    redirect = settings.MEDICARE_REDIRECT_URI
    mymedicare_login_url = settings.MEDICARE_LOGIN_URI
    redirect = req.pathname2url(redirect)
    state = generate_nonce()
    state = req.pathname2url(state)
    request.session['state'] = state
    mymedicare_login_url = "%s&state=%s&redirect_uri=%s" % (
        mymedicare_login_url, state, redirect)
    next_uri = request.GET.get('next', "")
    if request.user.is_authenticated():
        return HttpResponseRedirect(next_uri)
    AnonUserState.objects.create(state=state, next_uri=next_uri)
    if getattr(settings, 'ALLOW_CHOOSE_LOGIN', False):
        return HttpResponseRedirect(reverse('mymedicare-choose-login'))
    return HttpResponseRedirect(mymedicare_login_url)


@never_cache
def mymedicare_choose_login(request):
    mymedicare_login_uri = settings.MEDICARE_LOGIN_URI
    redirect = settings.MEDICARE_REDIRECT_URI
    redirect = req.pathname2url(redirect)
    aus = AnonUserState.objects.get(state=request.session['state'])
    mymedicare_login_uri = "%s&state=%s&redirect_uri=%s" % (
        mymedicare_login_uri, aus.state, redirect)
    context = {'next_uri': aus.next_uri,
               'mymedicare_login_uri': mymedicare_login_uri}
    return render(request, 'design_system/login.html', context)
