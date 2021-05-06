import logging
import random
import urllib.request as urllib_request

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.decorators.cache import never_cache
from rest_framework import status
from rest_framework.exceptions import NotFound, APIException
from urllib.parse import urlsplit, urlunsplit

from apps.dot_ext.loggers import (clear_session_auth_flow_trace,
                                  get_session_auth_flow_trace,
                                  set_session_auth_flow_trace_value,
                                  update_session_auth_flow_trace_from_state,
                                  update_instance_auth_flow_trace_with_state)
from apps.dot_ext.models import Approval
from apps.fhir.bluebutton.models import hash_hicn, hash_mbi
from apps.mymedicare_cb.models import (BBMyMedicareCallbackCrosswalkCreateException,
                                       BBMyMedicareCallbackCrosswalkUpdateException)
from .authorization import OAuth2ConfigSLSx
from .loggers import log_authenticate_start, log_authenticate_success
from .models import AnonUserState, get_and_update_user
from .validators import is_mbi_format_valid, is_mbi_format_synthetic

logger = logging.getLogger('hhs_server.%s' % __name__)


class BBMyMedicareCallbackAuthenticateSlsUserInfoValidateException(APIException):
    # BB2-237 custom exception
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


# For SLSx auth workflow info, see apps/mymedicare_db/README.md
def authenticate(request):
    # Update authorization flow from previously stored state in AuthFlowUuid instance in mymedicare_login().
    request_state = request.GET.get('relay')

    clear_session_auth_flow_trace(request)
    update_session_auth_flow_trace_from_state(request, request_state)

    # Get auth flow session values.
    auth_flow_dict = get_session_auth_flow_trace(request)

    # SLSx client instance
    slsx_client = OAuth2ConfigSLSx()

    request_token = request.GET.get('req_token', None)
    if request_token is None:
        log_authenticate_start(auth_flow_dict, "FAIL",
                               "SLSx request_token is missing in callback error.", slsx_client=slsx_client)
        raise ValidationError(settings.MEDICARE_ERROR_MSG)

    # Exchange req_token for access token
    slsx_client.exchange_for_access_token(request_token, request)

    # Get user_info
    user_info = slsx_client.get_user_info(request)

    # Signout bene to prevent SSO issues per BB2-544
    slsx_client.user_signout(request)

    # Validate bene is signed out per BB2-544
    slsx_client.validate_user_signout(request)

    # Set identity values from userinfo response.
    sls_subject = slsx_client.user_id.strip()
    sls_hicn = user_info.get("hicn", "").strip()
    #     Convert SLS's mbi to UPPER case.
    sls_mbi = user_info.get("mbi", "").strip().upper()
    sls_first_name = user_info.get('firstName', "")
    if sls_first_name is None:
        sls_first_name = ""
    sls_last_name = user_info.get('lastName', "")
    if sls_last_name is None:
        sls_last_name = ""
    sls_email = user_info.get('email', "")
    if sls_email is None:
        sls_email = ""

    # If MBI returned from SLSx is blank, set to None for hash logging
    if sls_mbi == "":
        sls_mbi = None

    # Validate: sls_subject cannot be empty. TODO: Validate format too.
    if sls_subject == "":
        err_msg = "User info sub cannot be empty"
        log_authenticate_start(auth_flow_dict, "FAIL", err_msg, slsx_client=slsx_client)
        raise BBMyMedicareCallbackAuthenticateSlsUserInfoValidateException(settings.MEDICARE_ERROR_MSG)

    # Validate: sls_hicn cannot be empty.
    if sls_hicn == "":
        err_msg = "User info HICN cannot be empty."
        log_authenticate_start(auth_flow_dict, "FAIL", err_msg, sls_subject, slsx_client=slsx_client)
        raise BBMyMedicareCallbackAuthenticateSlsUserInfoValidateException(settings.MEDICARE_ERROR_MSG)

    # Set Hash values once here for performance and logging.
    sls_hicn_hash = hash_hicn(sls_hicn)
    sls_mbi_hash = hash_mbi(sls_mbi)

    # Validate: sls_mbi format.
    #    NOTE: mbi return from SLS can be empty/None (so can use hicn for matching later)
    sls_mbi_format_valid, sls_mbi_format_msg = is_mbi_format_valid(sls_mbi)
    sls_mbi_format_synthetic = is_mbi_format_synthetic(sls_mbi)
    if not sls_mbi_format_valid and sls_mbi is not None:
        err_msg = "User info MBI format is not valid. "
        log_authenticate_start(auth_flow_dict, "FAIL", err_msg,
                               sls_subject, sls_mbi_format_valid,
                               sls_mbi_format_msg, sls_mbi_format_synthetic,
                               sls_hicn_hash, sls_mbi_hash, slsx_client)
        raise BBMyMedicareCallbackAuthenticateSlsUserInfoValidateException(settings.MEDICARE_ERROR_MSG)

    # Log successful identity information gathered.
    log_authenticate_start(auth_flow_dict, "OK", None, sls_subject,
                           sls_mbi_format_valid, sls_mbi_format_msg,
                           sls_mbi_format_synthetic, sls_hicn_hash, sls_mbi_hash, slsx_client)

    # Find or create the user associated with the identity information from SLS.
    user, crosswalk_action = get_and_update_user(subject=sls_subject,
                                                 mbi_hash=sls_mbi_hash,
                                                 hicn_hash=sls_hicn_hash,
                                                 first_name=sls_first_name,
                                                 last_name=sls_last_name,
                                                 email=sls_email, request=request)

    # Set crosswalk_action and get auth flow session values.
    set_session_auth_flow_trace_value(request, 'auth_crosswalk_action', crosswalk_action)
    auth_flow_dict = get_session_auth_flow_trace(request)

    # Log successful authentication with beneficiary when we return back here.
    log_authenticate_success(auth_flow_dict, sls_subject, user)

    # Update request user.
    request.user = user


@never_cache
def callback_v2(request):
    return callback(request, 2)


@never_cache
def callback(request, version=1):
    try:
        authenticate(request)
    except ValidationError as e:
        return JsonResponse({
            "error": e.message,
        }, status=status.HTTP_400_BAD_REQUEST)
    except NotFound as e:
        return TemplateResponse(
            request,
            "bene_404.html",
            context={
                "error": e.detail,
            },
            status=status.HTTP_404_NOT_FOUND)
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

    state = request.GET.get('relay')

    if not state:
        return JsonResponse({
            "error": 'The state parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        anon_user_state = AnonUserState.objects.get(state=state)
    except AnonUserState.DoesNotExist:
        return JsonResponse({"error": 'The requested state was not found'}, status=status.HTTP_400_BAD_REQUEST)
    next_uri = anon_user_state.next_uri

    scheme, netloc, path, query_string, fragment = urlsplit(next_uri)

    approval = Approval.objects.create(
        user=request.user)

    # Only go back to app authorization
    url_map_name = 'oauth2_provider_v2:authorize-instance-v2' if version == 2 else 'oauth2_provider:authorize-instance'
    auth_uri = reverse(url_map_name, args=[approval.uuid])

    _, _, auth_path, _, _ = urlsplit(auth_uri)
    return HttpResponseRedirect(urlunsplit((scheme, netloc, auth_path, query_string, fragment)))


def generate_nonce(length=26):
    """Generate pseudo-random number."""
    return ''.join([str(random.randint(0, 9)) for i in range(length)])


@never_cache
def mymedicare_login_v2(request):
    # not invoked by runtime, invoked by unittests only
    return mymedicare_login(request, 2)


@never_cache
def mymedicare_login(request, version=1):
    redirect = settings.MEDICARE_SLSX_REDIRECT_URI
    mymedicare_login_url = settings.MEDICARE_SLSX_LOGIN_URI

    # Perform health check on SLSx service
    slsx_client = OAuth2ConfigSLSx()
    slsx_client.service_health_check(request)

    relay_param_name = "relay"
    redirect = urllib_request.pathname2url(redirect)
    state = generate_nonce()
    state = urllib_request.pathname2url(state)
    request.session[relay_param_name] = state
    mymedicare_login_url = "%s&%s=%s&redirect_uri=%s" % (
        mymedicare_login_url, relay_param_name, state, redirect)
    next_uri = request.GET.get('next', "")

    AnonUserState.objects.create(state=state, next_uri=next_uri)

    # Update authorization flow trace AuthFlowUuid with state for pickup in authenticate().
    update_instance_auth_flow_trace_with_state(request, state)

    return HttpResponseRedirect(mymedicare_login_url)
