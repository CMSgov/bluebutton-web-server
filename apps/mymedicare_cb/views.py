from django.conf import settings
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth import login
import requests
from django.http import JsonResponse
import urllib.request as urllib_request
import random
from .models import (
    AnonUserState,
    get_and_update_user,
)
import logging
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from .authorization import OAuth2Config

logger = logging.getLogger('hhs_server.%s' % __name__)


@never_cache
def callback(request):

    state = request.GET.get('state')
    if not state:
        return JsonResponse({
            "error": 'The state parameter is required'
        }, status=400)

    try:
        anon_user_state = AnonUserState.objects.get(state=state)
    except AnonUserState.DoesNotExist:
        return JsonResponse({"error": 'The requested state was not found'}, status=400)
    next_uri = anon_user_state.next_uri

    code = request.GET.get('code')
    if not code:
        return JsonResponse({
            "error": 'The code parameter is required'
        }, status=400)

    sls_client = OAuth2Config()

    try:
        sls_client.exchange(code)
    except requests.exceptions.HTTPError as e:
        logger.error("Token request response error {reason}".format(reason=e))
        return JsonResponse({
            "error": 'An error occurred connecting to account.mymedicare.gov'
        }, status=502)

    userinfo_endpoint = getattr(
        settings,
        'SLS_USERINFO_ENDPOINT',
        'https://test.accounts.cms.gov/v1/oauth/userinfo')

    r = requests.get(userinfo_endpoint,
                     headers=sls_client.auth_header(),
                     verify=sls_client.verify_ssl)

    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logger.error("User info request response error {reason}".format(reason=e))
        return JsonResponse({
            "error": 'An error occurred connecting to account.mymedicare.gov'
        }, status=502)

    # Get the userinfo response object
    user_info = r.json()
    user = get_and_update_user(user_info)
    login(request, user)

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
