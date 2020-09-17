import logging
import random
import requests
import urllib.request as urllib_request
import datetime
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.decorators.cache import never_cache
from rest_framework.exceptions import NotFound
from urllib.parse import urlsplit, urlunsplit
from apps.dot_ext.loggers import (clear_session_auth_flow_trace,
                                  get_session_auth_flow_trace,
                                  set_session_auth_flow_trace_value,
                                  update_session_auth_flow_trace_from_state,
                                  update_instance_auth_flow_trace_with_state)
from apps.dot_ext.models import Approval
from apps.fhir.bluebutton.exceptions import UpstreamServerException
from apps.fhir.bluebutton.models import hash_hicn, hash_mbi
from apps.dot_ext.utils import get_app_and_org_by_client_id

from .authorization import OAuth2Config
from .loggers import log_authenticate_start, log_authenticate_success
from .models import AnonUserState, get_and_update_user
from .signals import response_hook_wrapper
from .validators import is_mbi_format_valid, is_mbi_format_synthetic
from apps.logging.serializers import SLSUserInfoResponse

logger = logging.getLogger('hhs_server.%s' % __name__)


# For SLS auth workflow info, see apps/mymedicare_db/README.md
def authenticate(request):
    # Standard error message returned to end user.
    ERROR_MSG_MYMEDICARE = "An error occurred connecting to account.mymedicare.gov"

    # Update authorization flow from previously stored state in AuthFlowUuid instance in mymedicare_login().
    request_state = request.GET.get('state', None)
    clear_session_auth_flow_trace(request)
    update_session_auth_flow_trace_from_state(request, request_state)

    # Get auth flow session values.
    auth_flow_dict = get_session_auth_flow_trace(request)

    code = request.GET.get('code')
    if not code:
        # Log for info
        err_msg = "The code parameter is required"
        log_authenticate_start(auth_flow_dict, "FAIL", err_msg)
        raise ValidationError(err_msg)

    sls_client = OAuth2Config()

    try:
        sls_client.exchange(code, request)
    except requests.exceptions.HTTPError as e:
        logger.error("Token request response error {reason}".format(reason=e))
        # Log also for info
        log_authenticate_start(auth_flow_dict, "FAIL",
                               "Token request response error {reason}".format(reason=e))
        raise UpstreamServerException(ERROR_MSG_MYMEDICARE)

    userinfo_endpoint = getattr(
        settings,
        'SLS_USERINFO_ENDPOINT',
        'https://test.accounts.cms.gov/v1/oauth/userinfo')

    headers = sls_client.auth_header()
    # keep using deprecated conv - no conflict issue
    headers.update({"X-SLS-starttime": str(datetime.datetime.utcnow())})
    auth_uuid, auth_app_name, auth_organization_name = None, None, None
    auth_app_id, auth_organization_id = None, None
    if request is not None:
        auth_uuid = request.session.get('auth_uuid', None)
        auth_app_name = request.session.get('auth_app_name', None)
        auth_app_id = request.session.get('auth_app_id', None)
        app, user = get_app_and_org_by_client_id(request.session.get('auth_client_id', None))
        auth_organization_name = user.username if user else ""
        auth_organization_id = str(user.id) if user else ""
        headers.update({"X-Request-ID": str(getattr(request, '_logging_uuid', None)
                        if hasattr(request, '_logging_uuid') else '')})
    response = requests.get(userinfo_endpoint,
                            headers=headers,
                            verify=sls_client.verify_ssl,
                            hooks={
                                'response': [
                                    response_hook_wrapper(sender=SLSUserInfoResponse,
                                                          auth_uuid=auth_uuid,
                                                          auth_app_name=auth_app_name,
                                                          auth_app_id=auth_app_id,
                                                          auth_organization_name=auth_organization_name,
                                                          auth_organization_id=auth_organization_id)]})

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logger.error("User info request response error {reason}".format(reason=e))
        # Log also for info
        log_authenticate_start(auth_flow_dict, "FAIL",
                               "User info request response error {reason}".format(reason=e))
        raise UpstreamServerException(ERROR_MSG_MYMEDICARE)

    # Get the userinfo response object
    user_info = response.json()

    # Set identity values from userinfo response.
    sls_subject = user_info.get("sub", None).strip()
    sls_hicn = user_info.get("hicn", "").strip()
    #     Convert SLS's mbi to UPPER case.
    sls_mbi = user_info.get("mbi", "").strip().upper()
    sls_first_name = user_info.get('given_name', "")
    sls_last_name = user_info.get('family_name', "")
    sls_email = user_info.get('email', "")

    # If MBI returned from SLS is blank, set to None for hash logging
    if sls_mbi == "":
        sls_mbi = None

    # Validate: sls_subject cannot be empty. TODO: Validate format too.
    if sls_subject == "":
        err_msg = "User info sub cannot be empty"
        log_authenticate_start(auth_flow_dict, "FAIL", err_msg)
        raise UpstreamServerException(ERROR_MSG_MYMEDICARE)

    # Validate: sls_hicn cannot be empty.
    if sls_hicn == "":
        err_msg = "User info HICN cannot be empty."
        log_authenticate_start(auth_flow_dict, "FAIL", err_msg, sls_subject)
        raise UpstreamServerException(ERROR_MSG_MYMEDICARE)

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
                               sls_hicn_hash, sls_mbi_hash)
        raise UpstreamServerException(ERROR_MSG_MYMEDICARE)

    # Log successful identity information gathered.
    log_authenticate_start(auth_flow_dict, "OK", None, sls_subject,
                           sls_mbi_format_valid, sls_mbi_format_msg,
                           sls_mbi_format_synthetic, sls_hicn_hash, sls_mbi_hash)

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

    # Update authorization flow trace AuthFlowUuid with state for pickup in authenticate().
    update_instance_auth_flow_trace_with_state(request, state)

    return HttpResponseRedirect(mymedicare_login_url)
