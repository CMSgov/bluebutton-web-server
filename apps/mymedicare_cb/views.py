import random
import urllib.request as urllib_request
import os
import requests
import time
from urllib.parse import parse_qs, unquote, urlsplit, urlunsplit


from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.decorators.cache import never_cache
from rest_framework import status
from rest_framework.exceptions import NotFound
from apps.constants import Versions

from apps.dot_ext.loggers import (clear_session_auth_flow_trace,
                                  set_session_auth_flow_trace_value,
                                  update_session_auth_flow_trace_from_state,
                                  update_instance_auth_flow_trace_with_state)
from apps.dot_ext.models import Approval
from apps.mymedicare_cb.models import (BBMyMedicareCallbackCrosswalkCreateException,
                                       BBMyMedicareCallbackCrosswalkUpdateException)
from apps.fhir.bluebutton.exceptions import UpstreamServerException
from .authorization import (OAuth2ConfigSLSx,
                            MedicareCallbackExceptionType,
                            BBMyMedicareCallbackAuthenticateSlsUserInfoValidateException)
from .models import AnonUserState, get_and_update_user


# For SLSx auth workflow info, see apps/mymedicare_db/README.md
def authenticate(request):
    # Update authorization flow from previously stored state in AuthFlowUuid instance in mymedicare_login().
    request_state = request.GET.get('relay')
    clear_session_auth_flow_trace(request)
    update_session_auth_flow_trace_from_state(request, request_state)

    # SLSx client instance
    slsx_client = OAuth2ConfigSLSx()

    request_token = request.GET.get('req_token', None)

    slsx_client.validate_asserts(request, [
        (request_token is None, "SLSx request_token is missing in callback error.")
    ], MedicareCallbackExceptionType.VALIDATION_ERROR)

    # Exchange req_token for access token
    slsx_client.exchange_for_access_token(request_token, request)

    # Get user_info. TODO: Move userinfo type validations in to this method.
    # get_user_info() will do validation, and then populate values from user info
    # e.g. first last name, email, sub (user_id), hicn, mbi, and their hashes etc.
    slsx_client.get_user_info(request)

    # Signout bene to prevent SSO issues per BB2-544
    slsx_client.user_signout(request)

    # Validate bene is signed out per BB2-544
    slsx_client.validate_user_signout(request)

    # Log successful identity information gathered.
    slsx_client.log_event(request, {})

    # Find or create the user associated with the identity information from SLS.
    user, crosswalk_action = get_and_update_user(slsx_client, request)

    # Set crosswalk_action and get auth flow session values.
    set_session_auth_flow_trace_value(request, 'auth_crosswalk_action', crosswalk_action)

    # Log successful authentication with beneficiary when we return back here.
    slsx_client.log_authn_success(request, {
        'user': {
            'id': user.id,
            'username': user.username,
            'crosswalk': {
                'id': user.crosswalk.id,
                'user_hicn_hash': user.crosswalk.user_hicn_hash,
                'user_mbi': user.crosswalk.user_mbi,
                'fhir_id_v2': user.crosswalk.fhir_id(Versions.V2),
                'fhir_id_v3': user.crosswalk.fhir_id(Versions.V3),
                'user_id_type': user.crosswalk.user_id_type,
            },
        },
    })

    # Update request user.
    request.user = user


@never_cache
def callback(request):
    state = request.GET.get('relay')
    if not state:
        return JsonResponse({"error": 'The state parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        anon_user_state = AnonUserState.objects.get(state=state)
    except AnonUserState.DoesNotExist:
        return JsonResponse({"error": 'The requested state was not found'}, status=status.HTTP_400_BAD_REQUEST)
    next_uri = anon_user_state.next_uri

    # We don't have a `version` coming back from auth. Therefore, we check
    # the authorize URL to find what version pathway we are on.
    version = Versions.NOT_AN_API_VERSION
    for supported_version in Versions.supported_versions():
        if f"/v{supported_version}/o/authorize" in next_uri:
            version = supported_version
            break

    request.session['version'] = version

    user_not_found_error = None
    try:
        authenticate(request)
    except ValidationError as e:
        return JsonResponse({
            "error": e.message,
        }, status=status.HTTP_400_BAD_REQUEST)
    except NotFound as e:
        # We can't immediately return because we need the next_uri
        user_not_found_error = e
    except BBMyMedicareCallbackAuthenticateSlsUserInfoValidateException as e:
        return JsonResponse({
            "error": e.detail,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except BBMyMedicareCallbackCrosswalkCreateException as e:
        return JsonResponse({
            "error": e.detail,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except BBMyMedicareCallbackCrosswalkUpdateException as e:
        return JsonResponse({
            "error": e.detail,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except UpstreamServerException:
        # Return more generic message to users to prevent oversharing information
        # Full error details will be available in logs from match_fhir_id
        return JsonResponse({
            "error": "Failed to retrieve data from data source."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    scheme, netloc, path, query_string, fragment = urlsplit(next_uri)

    if user_not_found_error:
        qs_dict = parse_qs(query_string)
        if 'redirect_uri' in qs_dict:
            redirect_uri = unquote(qs_dict['redirect_uri'][0])
            error_uri = f"{redirect_uri}?error=not_found"
        else:
            error_uri = None
        return TemplateResponse(
            request,
            "bene_404.html",
            context={
                "error_uri": error_uri,
                "error": user_not_found_error.detail,
                "request_id": request._logging_uuid,
            },
            status=status.HTTP_404_NOT_FOUND)

    approval = Approval.objects.create(user=request.user)

    # Only go back to app authorization
    if version == 3:
        url_map_name = 'oauth2_provider_v3:authorize-instance-v3'
    elif version == 2:
        url_map_name = 'oauth2_provider_v2:authorize-instance-v2'
    else:
        url_map_name = 'oauth2_provider:authorize-instance'
    auth_uri = reverse(url_map_name, args=[approval.uuid])

    _, _, auth_path, _, _ = urlsplit(auth_uri)
    return HttpResponseRedirect(urlunsplit((scheme, netloc, auth_path, query_string, fragment)))


def generate_nonce(length=26):
    """Generate pseudo-random number."""
    return ''.join([str(random.randint(0, 9)) for i in range(length)])


@never_cache
def mymedicare_login(request):
    redirect = settings.MEDICARE_SLSX_REDIRECT_URI
    mymedicare_login_url = settings.MEDICARE_SLSX_LOGIN_URI
    env = os.environ.get('TARGET_ENV')
    max_retries = 3
    retries = 0

    while retries <= max_retries:
        try:
            # Perform health check on SLSx service
            slsx_client = OAuth2ConfigSLSx()
            if slsx_client.service_health_check(request):
                break
        except requests.exceptions.ConnectionError as e:
            if retries < max_retries and (env is None or env == 'DEV'):
                time.sleep(0.5)
                retries += 1
            else:
                raise e

    relay_param_name = "relay"
    redirect = urllib_request.pathname2url(redirect)
    state = generate_nonce()
    state = urllib_request.pathname2url(state)
    request.session[relay_param_name] = state
    mymedicare_login_url = "%s&%s=%s&redirect_uri=%s" % (
        mymedicare_login_url, relay_param_name, state, redirect)
    # Check if language was saved server-side for this session
    language = request.session.get('auth_language', None)
    if language is not None:
        # Modify the Medicare login url according to the stored language
        if language == 'es':
            mymedicare_login_url += "&lang=es-mx"
        elif language == 'en':
            mymedicare_login_url += "&lang=en-us"
    next_uri = request.GET.get('next', '')

    AnonUserState.objects.create(state=state, next_uri=next_uri)

    # Update authorization flow trace AuthFlowUuid with state for pickup in authenticate().
    update_instance_auth_flow_trace_with_state(request, state)

    response = HttpResponseRedirect(mymedicare_login_url)
    if language is not None:
        # Set browser cookie so Django will translate authorization screen to correct language
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language)

    return response
