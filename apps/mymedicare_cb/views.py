from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.auth import login
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, JsonResponse
import requests

from apps.accounts.models import UserProfile
from apps.fhir.bluebutton.models import Crosswalk
from apps.fhir.bluebutton.utils import get_resourcerouter, FhirServerAuth
import urllib.request as urllib_request
from apps.fhir.authentication import convert_sls_uuid
import random
from .models import AnonUserState
import logging
from django.shortcuts import render
from django.views.decorators.cache import never_cache

logger = logging.getLogger('hhs_server.%s' % __name__)


@never_cache
def callback(request):
    token_endpoint = settings.SLS_TOKEN_ENDPOINT
    redirect_uri = settings.MEDICARE_REDIRECT_URI
    userinfo_endpoint = getattr(
        settings, 'SLS_USERINFO_ENDPOINT', 'https://dev.accounts.cms.gov/v1/oauth/userinfo')
    verify_ssl = getattr(settings, 'SLS_VERIFY_SSL', True)
    code = request.GET.get('code')
    state = request.GET.get('state')

    if not code:
        return JsonResponse({"error": 'The code parameter is required'}, status=400)

    if not state:
        return JsonResponse({"error": 'The state parameter is required'}, status=400)

    try:
        anon_user_state = AnonUserState.objects.get(state=state)
    except AnonUserState.DoesNotExist:
        return JsonResponse({"error": 'The requested state was not found'}, status=400)

    next_uri = anon_user_state.next_uri
    token_dict = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri}

    logger.debug("token_endpoint %s" % (token_endpoint))
    logger.debug("redirect_uri %s" % (redirect_uri))

    # Call SLS token endpoint
    token_response = requests.post(token_endpoint, json=token_dict, verify=verify_ssl)

    if token_response.status_code != 200:
        logger.error("Token request response error %s" % (token_response.status_code))
        logger.error("Details: %s" % (token_response.text))
        return JsonResponse({"error": 'An error occurred connecting to account.mymedicare.gov'}, status=502)

    headers = {"Authorization": "Bearer %s" % (token_response.json()['access_token'])}

    # Call SLS userinfo endpoint
    userinfo_response = requests.get(userinfo_endpoint, headers=headers, verify=verify_ssl)

    if userinfo_response.status_code != 200:
        logger.error("Userinfo request response error %s" % (userinfo_response.status_code))
        logger.error("Details: %s" % (userinfo_response.text))
        return JsonResponse({"error": 'An error occurred connecting to account.mymedicare.gov'}, status=502)

    # Get the userinfo response object
    user_info = userinfo_response.json()
    try:
        user = User.objects.get(username=convert_sls_uuid(user_info['sub']))
        if not user.first_name:
            user.first_name = user_info['given_name']
        if not user.last_name:
            user.last_name = user_info['family_name']
        if not user.email:
            user.email = user_info['email']
        user.save()
    except User.DoesNotExist:
        user = User(username=user_info['sub'][9:36], password='',
                    first_name=user_info['given_name'],
                    last_name=user_info['family_name'],
                    email=user_info['email'])
        user.save()

    UserProfile.objects.get_or_create(user=user, user_type='BEN')
    group = Group.objects.get(name='BlueButton')
    user.groups.add(group)

    # Log in the user
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)

    # Determine patient_id
    fhir_source = get_resourcerouter()
    crosswalk, _ = Crosswalk.objects.get_or_create(
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

    backend_response = requests.get(url, cert=certs, verify=False)
    backend_data = backend_response.json()

    if 'entry' in backend_data and backend_data['total'] == 1:
        fhir_id = backend_response.json()['entry'][0]['resource']['id']
        crosswalk.fhir_id = fhir_id
        crosswalk.save()

        logger.info("Success:Beneficiary connected to FHIR")
    else:
        logger.error("Failed to connect Beneficiary "
                     "to FHIR")

    # Get first and last name from FHIR if not in OIDC Userinfo response.
    if user_info['given_name'] == "" or user_info['family_name'] == "":
        if 'entry' in backend_data and 'name' in backend_data['entry'][0]['resource']:
            names = backend_data['entry'][0]['resource']['name']
            first_name = ""
            last_name = ""
            for name in names:
                if name['use'] == 'usual':
                    last_name = name['family']
                    first_name = name['given'][0]

                if last_name or first_name:
                    user.first_name = first_name
                    user.last_name = last_name
                    user.save()

    return HttpResponseRedirect(next_uri)


def generate_nonce(length=26):
    """Generate pseudo-random number."""
    return ''.join([str(random.randint(0, 9)) for i in range(length)])


@never_cache
def mymedicare_login(request):
    redirect = settings.MEDICARE_REDIRECT_URI
    mymedicare_login_url = settings.MEDICARE_LOGIN_URI
    redirect = urllib_request.pathname2url(redirect)
    state = generate_nonce()
    state = urllib_request.pathname2url(state)
    request.session['state'] = state
    mymedicare_login_url = "%s&state=%s&redirect_uri=%s" % (
        mymedicare_login_url, state, redirect)
    next_uri = request.GET.get('next', "")

    AnonUserState.objects.create(state=state, next_uri=next_uri)
    if getattr(settings, 'ALLOW_CHOOSE_LOGIN', False):
        return HttpResponseRedirect(reverse('mymedicare-choose-login'))

    return HttpResponseRedirect(mymedicare_login_url)


@never_cache
def mymedicare_choose_login(request):
    mymedicare_login_uri = settings.MEDICARE_LOGIN_URI
    redirect = settings.MEDICARE_REDIRECT_URI
    redirect = urllib_request.pathname2url(redirect)
    anon_user_state = AnonUserState.objects.get(state=request.session['state'])
    mymedicare_login_uri = "%s&state=%s&redirect_uri=%s" % (
        mymedicare_login_uri, anon_user_state.state, redirect)
    context = {'next_uri': anon_user_state.next_uri,
               'mymedicare_login_uri': mymedicare_login_uri}
    return render(request, 'design_system/login.html', context)
