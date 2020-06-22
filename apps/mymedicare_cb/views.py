from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
import requests
from django.http import JsonResponse
from django.template.response import TemplateResponse
import urllib.request as urllib_request
from urllib.parse import (
    urlsplit,
    urlunsplit,
)
import random
from .models import (
    AnonUserState,
    get_and_update_user,
)
from .validators import is_mbi_format_valid, is_mbi_format_synthetic
import logging
from django.core.exceptions import ValidationError
from rest_framework.exceptions import NotFound
from django.views.decorators.cache import never_cache
from .authorization import OAuth2Config
from .signals import response_hook
from apps.dot_ext.models import Approval
from apps.fhir.bluebutton.exceptions import UpstreamServerException

logger = logging.getLogger('hhs_server.%s' % __name__)
authenticate_logger = logging.getLogger('audit.authenticate.sls')


# For SLS auth workflow info, see apps/mymedicare_db/README.md
def authenticate(request):
    code = request.GET.get('code')
    if not code:
        raise ValidationError('The code parameter is required')

    sls_client = OAuth2Config()

    try:
        sls_client.exchange(code)
    except requests.exceptions.HTTPError as e:
        logger.error("Token request response error {reason}".format(reason=e))
        raise UpstreamServerException('An error occurred connecting to account.mymedicare.gov')

    userinfo_endpoint = getattr(
        settings,
        'SLS_USERINFO_ENDPOINT',
        'https://test.accounts.cms.gov/v1/oauth/userinfo')

    headers = sls_client.auth_header()
    headers.update({"X-Request-ID": getattr(request, '__logging_uuid', None)})
    response = requests.get(userinfo_endpoint,
                            headers=headers,
                            verify=sls_client.verify_ssl,
                            hooks={'response': response_hook})

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logger.error("User info request response error {reason}".format(reason=e))
        raise UpstreamServerException(
            'An error occurred connecting to account.mymedicare.gov')

    # Get the userinfo response object
    user_info = response.json()

    # Add MBI validation info for logging.
    sls_mbi = user_info.get("mbi","").upper()
    sls_mbi_format_valid, sls_mbi_format_msg = is_mbi_format_valid(sls_mbi)
    sls_mbi_format_synthetic = is_mbi_format_synthetic(sls_mbi)

    authenticate_logger.info({
        "type": "Authentication:start",
        "sub": user_info["sub"],
        "sls_mbi_format_valid": sls_mbi_format_valid,
        "sls_mbi_format_msg": sls_mbi_format_msg,
        "sls_mbi_format_synthetic": sls_mbi_format_synthetic,
    })

    user = get_and_update_user(user_info)

    authenticate_logger.info({
        "type": "Authentication:success",
        "sub": user_info["sub"],
        "user": {
            "id": user.id,
            "username": user.username,
            "crosswalk": {
                "id": user.crosswalk.id,
                "user_hicn_hash": user.crosswalk.user_hicn_hash,
                "user_mbi_hash": user.crosswalk.user_mbi_hash,
                "fhir_id": user.crosswalk.fhir_id,
                "user_id_type": user.crosswalk.user_id_type,
            },
        },
    })
    request.user = user


@never_cache
def callback(request):
    try:
        authenticate(request)
    except ValidationError as e:
        return JsonResponse({
            "error": e.message,
        }, status=400)
    except NotFound as e:
        return TemplateResponse(
            request,
            "bene_404.html",
            context={
                "error": e.detail,
            },
            status=404)
    except UpstreamServerException as e:
        return JsonResponse({
            "error": e.detail,
        }, status=502)

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

    scheme, netloc, path, query_string, fragment = urlsplit(next_uri)

    approval = Approval.objects.create(
        user=request.user)

    # Only go back to app authorization
    auth_uri = reverse('oauth2_provider:authorize-instance', args=[approval.uuid])
    _, _, auth_path, _, _ = urlsplit(auth_uri)

    return HttpResponseRedirect(urlunsplit((scheme, netloc, auth_path, query_string, fragment)))


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

    return HttpResponseRedirect(mymedicare_login_url)
