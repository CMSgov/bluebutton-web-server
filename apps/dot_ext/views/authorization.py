from http import HTTPStatus
from datetime import datetime, timedelta, timezone
from functools import wraps
import re
from time import strftime

import uuid
import html
import json
import logging
import jwt

from django.contrib.auth import get_user_model
from django.contrib.auth.views import redirect_to_login
from django.http import JsonResponse, HttpRequest
from django.http.response import HttpResponse, HttpResponseBadRequest
from django.template.response import TemplateResponse
from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters
from apps.fhir.bluebutton.exceptions import UpstreamServerException
from oauth2_provider.exceptions import OAuthToolkitError
from apps.fhir.bluebutton.models import Crosswalk
from oauth2_provider.views.base import app_authorized
from oauth2_provider.views.base import AuthorizationView as DotAuthorizationView
from oauth2_provider.views.base import TokenView as DotTokenView
from oauth2_provider.views.base import RevokeTokenView as DotRevokeTokenView
from oauth2_provider.views.introspect import IntrospectTokenView as DotIntrospectTokenView
from waffle import switch_is_active, get_waffle_flag_model
from oauth2_provider.models import get_access_token_model, get_application_model, get_refresh_token_model
from oauthlib.oauth2 import AccessDeniedError
from oauthlib.oauth2.rfc6749.errors import InvalidClientError, InvalidGrantError, InvalidRequestError
from rest_framework.exceptions import NotFound
from urllib.parse import urlparse, parse_qs
from apps.dot_ext.scopes import CapabilitiesScopes
from apps.fhir.server.settings import fhir_settings
from apps.mymedicare_cb.models import get_and_update_from_refresh
from apps.constants import APPLICATION_DOES_NOT_HAVE_V3_ENABLED_YET, HHS_SERVER_LOGNAME_FMT
from apps.dot_ext.constants import (
    APPLICATION_DOES_NOT_HAVE_CLIENT_CREDENTIALS_ENABLED, CLIENT_CREDENTIALS_ACCEPTED_JWT_ALGORITHMS,
    CLIENT_ASSERTION_TYPE_VALUE, JWKS_URLS, CSP_IAL_ACCEPTED_JWT_ALGORITHMS, YYYY_MM_DD_REGEX, CC_SYSTEM_CODING_SYSTEM,
    CC_SYSTEM_SOCIAL_SECURITY_NUMBER
)
from apps.versions import Versions
from jwt import PyJWKClient
from apps.dot_ext.signals import beneficiary_authorized_application
from apps.dot_ext.forms import SimpleAllowForm
from apps.dot_ext.loggers import (
    create_session_auth_flow_trace,
    cleanup_session_auth_flow_trace,
    get_session_auth_flow_trace,
    set_session_auth_flow_trace,
    set_session_auth_flow_trace_value,
    update_instance_auth_flow_trace_with_code,
)
from apps.dot_ext.models import Application, Approval
from apps.dot_ext.utils import (
    get_api_version_number_from_url,
    remove_application_user_pair_tokens_data_access,
    validate_app_is_active,
    json_response_from_oauth2_error,
    validate_latin_extended_string
)
from apps.authorization.models import DataAccessGrant
from fhir.resources.R4B.parameters import Parameters, ParametersParameter
from fhir.resources.R4B.patient import Patient
from fhir.resources.R4B.humanname import HumanName
from fhir.resources.R4B.contactpoint import ContactPoint
from fhir.resources.R4B.address import Address
from fhir.resources.R4B.identifier import Identifier
from fhir.resources.R4B.codeableconcept import CodeableConcept
from fhir.resources.R4B.coding import Coding

log = logging.getLogger(HHS_SERVER_LOGNAME_FMT.format(__name__))

QP_CHECK_LIST = ["client_secret"]


def get_grant_expiration(data_access_type):
    pass


def require_post_state_decorator(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        # Only enforce for the base /authorize/ (no uuid in the match)
        rm = getattr(request, "resolver_match", None)
        if request.method == "POST" and rm and "uuid" not in getattr(rm, "kwargs", {}):
            if not request.POST.get("state"):
                return JsonResponse(
                    {"status_code": 401, "message": "State required in POST body."},
                    status=401,
                )
        return view_func(request, *args, **kwargs)
    return _wrapped


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(require_post_state_decorator, name="dispatch")
class AuthorizationView(DotAuthorizationView):
    """
    Override the base authorization view from dot to
    use the custom AllowForm. Supports both GET and POST
    for OAuth params (query string OR form body).
    """
    # TODO: rename this so that it isn't the same as self.version (works but confusing)
    # this needs to be here for urls.py as_view(version) calls, but don't use it
    version = 0
    # Variable to help reduce the amount of times validate_v3_authorization_request is called
    form_class = SimpleAllowForm
    login_url = "/mymedicare/login"

    def __init__(self, version=1):
        self.version = version
        super().__init__()

    def _get_param(self, request, key, default=None):
        """Fetch a param from GET first, then POST."""
        return request.GET.get(key, request.POST.get(key, default))

    def _has_param(self, request, key):
        """True if param exists in either GET or POST."""
        return (key in request.GET) or (key in request.POST)

    def _check_for_required_params(self, request):
        missing_params = []
        v3 = True if request.path.startswith('/v3/o/authorize') else False

        if not request.GET.get('code_challenge', None):
            missing_params.append("code_challenge")
        if not request.GET.get('code_challenge_method', None):
            missing_params.append("code_challenge_method")

        if not request.GET.get('state', None):
            missing_params.append("state")
        elif len(request.GET.get('state', None)) < 16:
            error_message = "State parameter should have a minimum of 16 characters"
            return JsonResponse({"status_code": 400, "message": error_message}, status=400)

        # BB2-4250: This code will not execute if the application is not in the v3_early_adopter flag
        # so it will not be modified as part of BB2-4250
        if switch_is_active('v3_endpoints') and v3:
            if 'scope' not in request.GET:
                missing_params.append("scope")

        if missing_params:
            return JsonResponse({
                "status_code": 400,
                "message": f"Missing Required Parameter(s): {', '.join(missing_params)}"
            }, status=400)
        else:
            return None

    def get_context_data(self, **kwargs):
        context = super(AuthorizationView, self).get_context_data(**kwargs)
        context['permission_end_date_text'] = self.application.access_end_date_text()
        context['permission_end_date'] = self.application.access_end_date()
        return context

    def dispatch(self, request, *args, **kwargs):
        """
        Override the base authorization view from dot to
        initially create an AuthFlowUuid object for authorization
        flow tracing in logs.
        """
        path_info = self.request.__dict__.get('path_info')
        version = get_api_version_number_from_url(path_info)
        # If it is not version 3, we don't need to check anything, just return
        if version == Versions.V3:
            try:
                self.validate_v3_authorization_request()
            except AccessDeniedError as e:
                return JsonResponse(
                    {'status_code': 403, 'message': str(e)},
                    status=403,
                )

        # TODO: Should the client_id match a valid application here before continuing, instead of after matching to FHIR_ID?
        if not kwargs.get('is_subclass_approvalview', False):
            # Create new authorization flow trace UUID in session and AuthFlowUuid instance, if subclass is not ApprovalView
            create_session_auth_flow_trace(request)

        try:
            self.application = validate_app_is_active(request)
        except InvalidClientError as error:
            return TemplateResponse(
                request,
                "app_inactive_401.html",
                context={
                    "detail": error.error + " : " + error.description,
                },
                status=error.status_code)

        sensitive_info_detected = self.sensitive_info_check(request)

        # Return early 4xx HttpResponseBadRequest if illegal query parameters detected
        if sensitive_info_detected:
            return sensitive_info_detected

        request.session['version'] = self.version

        # Accept lang from GET or POST
        lang = self._get_param(request, 'lang')
        if lang in ('en', 'es'):
            request.session['auth_language'] = lang

        if request.method == "POST" and not request.user.is_authenticated:
            post_qs = request.POST.urlencode()
            # preserve existing query too
            existing_qs = request.META.get("QUERY_STRING", "")
            merged_qs = f"{existing_qs}&{post_qs}" if existing_qs else post_qs
            next_url = f"{request.path}?{merged_qs}"
            return redirect_to_login(next_url, login_url=self.login_url)

        return super().dispatch(request, *args, **kwargs)

    def sensitive_info_check(self, request):
        for qp in QP_CHECK_LIST:
            if self._has_param(request, qp):
                return HttpResponseBadRequest(f"Illegal query parameter [{qp}] detected")
        return None

    def get_template_names(self):
        # Default template
        default_tpl = "design_system/new_authorize_v2.html"

        if not switch_is_active("enable_coverage_only"):
            return [default_tpl]

        app = getattr(self, "application", None)
        if app is not None and "coverage-eligibility" in app.get_internal_application_labels():
            return ["design_system/authorize_v3_coverage_only.html"]

        return [default_tpl]

    def get_initial(self):
        initial_data = super().get_initial()
        # Prefer values parsed by DOT (self.oauth2_data); fall back to incoming request (GET/POST)
        initial_data["code_challenge"] = (
            self.oauth2_data.get("code_challenge", None)
            or self._get_param(self.request, "code_challenge")
        )
        initial_data["code_challenge_method"] = (
            self.oauth2_data.get("code_challenge_method")
            or self._get_param(self.request, "code_challenge_method")
        )
        return initial_data

    def post(self, request, *args, **kwargs):
        kwargs['code_challenge'] = request.POST.get('code_challenge')
        kwargs['code_challenge_method'] = request.POST.get('code_challenge_method')
        return super().post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        param_check = self._check_for_required_params(request)
        if param_check:
            return param_check
        kwargs['code_challenge'] = request.GET.get('code_challenge', None)
        kwargs['code_challenge_method'] = request.GET.get('code_challenge_method', None)
        return super().get(request, *args, **kwargs)

    def validate_v3_authorization_request(self):
        flag = get_waffle_flag_model().get('v3_early_adopter')
        req_meta = self.request.META
        url_query = parse_qs(req_meta.get('QUERY_STRING'))
        client_id = url_query.get('client_id', [None])
        try:
            application = get_application_model().objects.get(client_id=client_id[0])
            application_user = get_user_model().objects.get(id=application.user_id)

            if flag.id is None or flag.is_active_for_user(application_user):
                # Update the class variable to ensure subsequent calls to dispatch don't call this function
                # more times than is needed
                return
            else:
                raise AccessDeniedError(
                    description=APPLICATION_DOES_NOT_HAVE_V3_ENABLED_YET.format(application.name)
                )
        except ObjectDoesNotExist:
            raise AccessDeniedError(
                description='Unable to verify permission.'
            )

    def form_valid(self, form):
        client_id = form.cleaned_data["client_id"]
        application = get_application_model().objects.get(client_id=client_id)
        credentials = {
            "client_id": form.cleaned_data.get("client_id"),
            "redirect_uri": form.cleaned_data.get("redirect_uri"),
            "response_type": form.cleaned_data.get("response_type", None),
            "state": form.cleaned_data.get("state", None),
            # "code_challenge": form.cleaned_data.get("code_challenge", None),
            # "code_challenge_method": form.cleaned_data.get("code_challenge_method", None),
        }

        if form.cleaned_data.get("code_challenge"):
            credentials["code_challenge"] = form.cleaned_data.get("code_challenge")

        if form.cleaned_data.get("code_challenge_method"):
            credentials["code_challenge_method"] = form.cleaned_data.get("code_challenge_method")

        scopes = form.cleaned_data.get("scope")
        allow = form.cleaned_data.get("allow")

        # Get beneficiary demographic scopes sharing choice
        share_demographic_scopes = form.cleaned_data.get("share_demographic_scopes")
        set_session_auth_flow_trace_value(self.request, 'auth_share_demographic_scopes', share_demographic_scopes)

        # Get scopes list available to the application
        application_available_scopes = CapabilitiesScopes().get_available_scopes(application=application)

        # Set scopes to those available to application and beneficiary demographic info choices
        scopes = ' '.join([s for s in scopes.split(" ")
                          if s in application_available_scopes])

        # Init deleted counts
        data_access_grant_delete_cnt = 0
        access_token_delete_cnt = 0
        refresh_token_delete_cnt = 0

        try:

            if not scopes:
                # Since the create_authorization_response will re-inject scopes even when none are
                # valid, we want to pre-emptively treat this as an error case
                raise OAuthToolkitError(
                    error=AccessDeniedError(state=credentials.get("state", None)), redirect_uri=credentials["redirect_uri"]
                )
            uri, headers, body, status = self.create_authorization_response(
                request=self.request, scopes=scopes, credentials=credentials, allow=allow
            )
        except OAuthToolkitError as error:
            response = self.error_response(error, application)
            if not scopes:
                (data_access_grant_delete_cnt,
                 access_token_delete_cnt,
                 refresh_token_delete_cnt) = remove_application_user_pair_tokens_data_access(application, self.request.user)

            beneficiary_authorized_application.send(
                sender=self,
                request=self.request,
                auth_status="FAIL",
                auth_status_code=response.status_code,
                user=self.request.user,
                application=application,
                share_demographic_scopes=share_demographic_scopes,
                scopes=scopes,
                allow=allow,
                access_token_delete_cnt=access_token_delete_cnt,
                refresh_token_delete_cnt=refresh_token_delete_cnt,
                data_access_grant_delete_cnt=data_access_grant_delete_cnt)
            return response

        # Did the beneficiary choose not to share demographic scopes, or the application does not require them?
        if share_demographic_scopes == "False" or (allow is True and application.require_demographic_scopes is False):
            (data_access_grant_delete_cnt,
             access_token_delete_cnt,
             refresh_token_delete_cnt) = remove_application_user_pair_tokens_data_access(application, self.request.user)

        beneficiary_authorized_application.send(
            sender=self,
            request=self.request,
            auth_status="OK",
            auth_status_code=None,
            user=self.request.user,
            application=application,
            share_demographic_scopes=share_demographic_scopes,
            scopes=scopes,
            allow=allow,
            access_token_delete_cnt=access_token_delete_cnt,
            refresh_token_delete_cnt=refresh_token_delete_cnt,
            data_access_grant_delete_cnt=data_access_grant_delete_cnt)

        self.success_url = uri
        log.debug("Success url for the request: {0}".format(self.success_url))

        # Extract code from url
        url_query = parse_qs(urlparse(self.success_url).query)
        code = url_query.get('code', [None])[0]

        # Get auth flow trace session values dict.
        auth_dict = get_session_auth_flow_trace(self.request)

        # We are done using auth_uuid, clear it from the session.
        cleanup_session_auth_flow_trace(self.request)

        # Update AuthFlowUuid instance with code.
        update_instance_auth_flow_trace_with_code(auth_dict, code)

        return self.redirect(self.success_url, application)


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(require_post_state_decorator, name="dispatch")
class ApprovalView(AuthorizationView):
    """
    Override the base authorization view from dot to
    use the custom AllowForm.
    """
    # TODO: rename this so that it isn't the same as self.version (works but confusing)
    # this needs to be here for urls.py as_view(version) calls, but don't use it
    version = 0
    form_class = SimpleAllowForm
    login_url = "/mymedicare/login"

    def __init__(self, version):
        self.version = version
        super().__init__(version=version)

    def is_valid_uuid(self, value: str) -> bool:
        try:
            uuid.UUID(str(value))
            return True
        except ValueError:
            return False

    def dispatch(self, request, uuid, *args, **kwargs):
        # BB2-4326: If we do not receive a valid uuid in the authorize call, throw a 404
        if not self.is_valid_uuid(uuid):
            return JsonResponse(
                {'status_code': 404, 'message': 'Not found.'},
                status=404,
            )

        # Get auth_uuid to set again after super() return. It gets cleared out otherwise.
        auth_flow_dict = get_session_auth_flow_trace(request)
        try:
            approval = Approval.objects.get(uuid=uuid)
            if approval.expired:
                raise Approval.DoesNotExist
            if (
                approval.application
                and approval.application.client_id != request.GET.get('client_id', None)
                and approval.application.client_id != request.POST.get('client_id', None)
            ):
                raise Approval.DoesNotExist
            request.user = approval.user
        except Approval.DoesNotExist:
            pass

        # Set flag to let super method know who's calling, so auth_uuid doesn't get reset.
        kwargs['is_subclass_approvalview'] = True

        request.session['version'] = self.version

        result = super().dispatch(request, *args, **kwargs)

        if hasattr(result, "headers") \
                and "Location" in result.headers \
                and "invalid_scope" in result.headers['Location']:
            return JsonResponse({"status_code": 400, "message": "Invalid scopes."}, status=400)

        if hasattr(self, 'oauth2_data'):
            application = self.oauth2_data.get('application', None)
            if application is not None:
                approval.application = self.oauth2_data.get('application', None)
                approval.save()

        # Set auth_uuid after super() return
        if auth_flow_dict:
            set_session_auth_flow_trace(request, auth_flow_dict)

        return result


@method_decorator(csrf_exempt, name="dispatch")
class TokenView(DotTokenView):

    def _validate_v3_token_call(self, request: HttpRequest) -> None:
        flag = get_waffle_flag_model().get('v3_early_adopter')

        try:
            url_query = parse_qs(request._body.decode('utf-8'))
            refresh_token_from_request = url_query.get('refresh_token', [None])
            refresh_token = get_refresh_token_model().objects.get(token=refresh_token_from_request[0])
            application = get_application_model().objects.get(id=refresh_token.application_id)
            application_user = get_user_model().objects.get(id=application.user_id)

            if flag.id is None or flag.is_active_for_user(application_user):
                return
            else:
                raise AccessDeniedError(
                    description=APPLICATION_DOES_NOT_HAVE_V3_ENABLED_YET.format(application.name)
                )
        except ObjectDoesNotExist:
            raise AccessDeniedError(
                description='Unable to verify permission.'
            )

    def _check_if_client_credentials_call_is_allowed(self, app: Application, version: Versions) -> bool:
        """Checks if the version fo the call is v3 + the app is allowed to do this and has a jwks_uri

        Args:
            app (Application): model
            version (Versions): Version constant

        Returns:
            bool: if the app is allowed to make a client_credential call
        """
        if version != Versions.V3:
            log.warning(f'A client_credentials token call was made for version: {version}')
            return False
        return app.allow_client_credentials and app.jwks_uri is not None

    def _validate_client_credentials_request(self, request: HttpRequest):
        """Checks required params for a client_credential request and their values

        Args:
            request (HttpRequest): the Django request object

        Raises:
            InvalidRequestError: if client_assertion_type is not correct

        Returns:
            JsonResponse or None: Returns a 400 error response if params are missing, else None
        """

        # TODO: grant_type is already implied, but I figured I'd follow the spec
        required_params = ['grant_type', 'scope', 'client_assertion_type', 'client_assertion']
        missing_params = [param for param in required_params if not request.POST.get(param)]

        if missing_params:
            return JsonResponse({
                'status_code': 400,
                'message': f"Missing Required Parameter(s): {', '.join(missing_params)}"
            }, status=400)

        if request.POST.get('client_assertion_type') != CLIENT_ASSERTION_TYPE_VALUE:
            log.warning(f'client_assertion_type was {request.POST.get('client_assertion_type')}')
            raise InvalidRequestError

        # TODO: do we have a function to validate scopes against BBAPI's well-known config?
        return None

    def _validate_authorization_jwt(self, token: str, jwks_client: PyJWKClient) -> str:
        """Validates an authorization JWT and returns the id_token if valid

        Args:
            token (str): the base64 encoded auth jwt
            jwks_client (PyJWKClient): instantiated client for the authorization jwt

        Raises:
            InvalidRequestError: any jwt error throws this

        Returns:
            str: the cms_smart extension's id_token
        """
        try:
            signing_key = jwks_client.get_signing_key_from_jwt(token)  # type: ignore
            # pyjwt handles:
            # header - alg, kid
            # payload - iss, aud, exp
            data = jwt.decode_complete(  # type: ignore
                token,
                signing_key,
                # issuer=app.client_id,
                audience=fhir_settings.fhir_url_v3,
                # leeway=timedelta(minutes=5),
                options={
                    'require': ['iss', 'sub', 'aud', 'jti', 'exp', 'extensions']
                },
                algorithms=CLIENT_CREDENTIALS_ACCEPTED_JWT_ALGORITHMS,
            )
            payload, header = data.get('payload'), data.get('header')

            if not payload or not header or header.get('typ') != 'JWT':
                log.warning('Malformed JWT')
                raise InvalidRequestError

            # TODO: combine iss and jti for cache + not allowed duplicates

            # payload
            if payload.get('exp') - datetime.now(timezone.utc).timestamp() > 300:
                log.warning('JWT exp is longer than 5 minutes away')
                raise InvalidRequestError

            # cms_smart extension
            cms_smart = payload.get('extensions', {}).get('cms_smart')
            if not cms_smart:
                log.warning('No CMS_Smart extension')
                raise InvalidRequestError

            if (
                cms_smart.get('version') != 1
                or cms_smart.get('purpose_of_use') != 'PATRQT'
                or not cms_smart.get('id_token')
            ):
                log.warning('Malformed CMS_Smart extension')
                raise InvalidRequestError

            return cms_smart.get('id_token')

        except (jwt.MissingRequiredClaimError, jwt.ExpiredSignatureError, jwt.InvalidIssuerError,
                jwt.InvalidAudienceError, jwt.InvalidKeyError, jwt.InvalidAlgorithmError) as e:
            log.warning(f'jwt.decode_complete() failed because {str(e)}')
            raise InvalidRequestError

    def _validate_ial_jwt(self, id_token: str, jwks_client: PyJWKClient) -> dict:
        """Validates an IAL JWT from a trusted CSP

        Args:
            id_token (str): base64 encoded id_token jwt from cms_smart extension
            jwks_client (PyJWKClient): instantiated client for the authorization jwt

        Raises:
            InvalidRequestError: if any validation step fails, log and raise

        Returns:
            str: the decoded payload of the IAL JWT
        """
        try:
            signing_key = jwks_client.get_signing_key_from_jwt(id_token)
            data = jwt.decode_complete(
                id_token,
                signing_key,
                leeway=timedelta(minutes=5),
                options={
                    'require': ['iss', 'sub', 'aud', 'jti', 'exp', 'iat',
                                'identity_assurance_level', 'auth_time'
                                'family_name', 'given_name', 'birthdate']
                },
                algorithms=CSP_IAL_ACCEPTED_JWT_ALGORITHMS
            )
            payload, header = data.get('payload'), data.get('header')

            if not payload or not header or header.get('typ') != 'JWT':
                log.warning('Malformed header / payload')
                raise InvalidRequestError

            # TODO: combine iss and jti for cache + not allowed duplicates

            # validation
            if datetime.now(timezone.utc).timestamp() - payload.get('iat') > 300:
                log.warning('JWT is older than 5 minutes (iat)')
                raise InvalidRequestError

            if payload.get('identity_assurance_level') != 2:
                log.warning(f'identity_assurance_level was invalid: {payload.get('identity_assurance_level')}')
                raise InvalidRequestError

            if datetime.now(timezone.utc).timestamp() - payload.get('auth_time') > 86400:
                log.warning('JWT was authorized older than 24 hours (auth_time)')
                raise InvalidRequestError

            if validate_latin_extended_string(payload.get('family_name')):
                log.warning(f'family_name is empty or has encoded characters greater than 383: {payload.get('family_name')}')
                raise InvalidRequestError

            if validate_latin_extended_string(payload.get('given_name')):
                log.warning(f'given_name is empty or has encoded characters greater than 383: {payload.get('given_name')}')
                raise InvalidRequestError

            if re.match(YYYY_MM_DD_REGEX, payload.get('birthdate')):
                log.warning(f'birthdate was not a valid string: {payload.get('birthdate')}')
                raise InvalidRequestError

            return payload
        except (jwt.MissingRequiredClaimError, jwt.ExpiredSignatureError, jwt.InvalidIssuerError,
                jwt.InvalidAudienceError, jwt.InvalidKeyError, jwt.InvalidAlgorithmError) as e:
            log.warning(f'jwt.decode_complete() failed because {str(e)}')
            raise InvalidRequestError

    def _parse_ial_into_parameter(self, payload: dict) -> Parameters:
        """Parses an IAL token into a Patient and Parameters resource

        Args:
            payload (dict): the IAL token

        Returns:
            Parameters: a Parameters object containing the Patient
        """
        patient = Patient.model_construct()
        patient.active = True

        patient_name = HumanName.model_construct()
        patient_name.use = 'official'
        patient_name.family = payload.get('family_name')
        patient_name.given = [payload.get('given_name')]

        patient.name = [patient_name]

        telecoms = []
        if payload.get('phone_number') and payload.get('phone_number_verified'):
            phone = ContactPoint.model_construct()
            phone.system = 'phone'
            phone.value = payload.get('phone_number')
            phone.use = 'mobile'
            phone.rank = 1
            telecoms.append(phone)

        if payload.get('email'):
            email = ContactPoint.model_construct()
            email.system = 'email'
            email.value = payload.get('email')
            email.use = 'home'
            email.rank = 2
            telecoms.append(email)

        patient.telecom = telecoms

        gender_map = {'f': 'female', 'm': 'male', 'o': 'other', 'u': 'unknown'}
        if payload.get('gender'):
            patient.gender = gender_map.get(payload.get('gender', 'u'))

        patient.birthDate = payload.get('birthdate')

        addresses = []
        # Home Address
        if (home := payload.get('address')):
            home_address = Address.model_construct()
            home_address.use = 'home'
            home_address.type = 'both'
            home_address.text = home.get('formatted')
            home_address.line = [street_address] if (street_address := home.get('street_address')) else None
            home_address.city = home.get('locality')
            home_address.state = home.get('region')
            home_address.postalCode = home.get('postal_code')
            home_address.country = home.get('country')
            addresses.append(home_address)

        # Historical Addresses
        for historical in payload.get('historical_address', []):
            hist_address = Address.model_construct()
            hist_address.use = 'old'
            hist_address.type = 'both'
            hist_address.text = historical.get('formatted')
            hist_address.line = [street_address] if (street_address := historical.get('street_address')) else None
            hist_address.city = historical.get('locality')
            hist_address.state = historical.get('region')
            hist_address.postalCode = historical.get('postal_code')
            hist_address.country = 'US'
            addresses.append(historical)

        patient.address = addresses

        if (ssn := payload.get('ssn_itin_short') or payload.get('SSN', '')[-4:]) and len(ssn) > 4:
            ssn_identifier = Identifier.model_construct()
            ssn_identifier.use = 'official'
            ssn_type = CodeableConcept.model_construct()
            ssn_coding = Coding.model_construct()
            ssn_coding.system = CC_SYSTEM_CODING_SYSTEM
            ssn_coding.code = 'SS'
            ssn_coding.display = 'Social Security Number'
            ssn_type.coding = [ssn_coding]
            ssn_identifier.type = ssn_type
            ssn_identifier.system = CC_SYSTEM_SOCIAL_SECURITY_NUMBER
            ssn_identifier.value = ssn
            patient.identifier = [ssn_identifier]

        id_match_payload = Parameters.model_construct()
        id_match_payload.parameter = [ParametersParameter(**{
            'name': 'IDIPatient',
            'resource': patient
        })]

        return id_match_payload

    @method_decorator(sensitive_post_parameters('password'))
    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        version = get_api_version_number_from_url(self.request.path_info)
        grant_type = request.POST.get('grant_type')
        try:
            # If it is not version 3, we don't need to check that the application is in the v3_early_adopter flag,
            # just continue with standard validation.
            # Also, we only want to execute this on refresh_token grant types, not authorization_code
            if version == Versions.V3 and grant_type == 'refresh_token':
                self._validate_v3_token_call(request)
            app = validate_app_is_active(request)

            if grant_type == 'client_credentials':
                # Check for malformed request
                request_validation_result = self._validate_client_credentials_request(request)
                if request_validation_result:
                    return request_validation_result
                allow_client_credentials_call = self._check_if_client_credentials_call_is_allowed(app, version)

                if allow_client_credentials_call:
                    try:
                        # Top level (application authorization) JWT validation
                        id_token = self._validate_authorization_jwt(
                            request.POST.get('client_assertion', ''), PyJWKClient(app.jwks_uri))

                        # Determine if this is CLEAR or ID.ME
                        pre_verified_ial = jwt.decode(id_token, options={'verify_signature': False})
                        csp_jwks = JWKS_URLS.get(pre_verified_ial.get('iss', ''))

                        if not csp_jwks:
                            log.warning(f'id_token did not have a valid iss: {pre_verified_ial.get('iss')}')
                            raise InvalidGrantError

                        ial_valid = self._validate_ial_jwt(id_token, PyJWKClient(csp_jwks))
                        if not ial_valid:
                            # at the moment, any validation error raises the exception inside
                            # probably refactor moment
                            raise InvalidRequestError

                        id_match_payload = self._parse_ial_into_parameter(ial_valid)

                        log.info(id_match_payload.model_dump_json())
                        log.info(f'client_credentials token call was successfully made for app: {app.name}')
                    except Exception as e:
                        log.error(f'Error validating jwt: {str(e)}')
                else:
                    error_message = APPLICATION_DOES_NOT_HAVE_CLIENT_CREDENTIALS_ENABLED.format(app.name)
                    return JsonResponse({'status_code': 400, 'message': error_message}, status=400)

        except (InvalidClientError, InvalidGrantError, InvalidRequestError) as error:
            return json_response_from_oauth2_error(error)
        except AccessDeniedError as e:
            return JsonResponse(
                {'status_code': 403, 'message': str(e)},
                status=403,
            )

        url, headers, body, status = self.create_token_response(request)

        if status == 200:
            body = json.loads(body)
            access_token = body.get('access_token')

            dag_expiry = ""
            if access_token is not None:
                token = get_access_token_model().objects.get(
                    token=access_token)
                app_authorized.send(
                    sender=self, request=request,
                    token=token)

                if app.data_access_type == "THIRTEEN_MONTH":
                    try:
                        dag = DataAccessGrant.objects.get(
                            beneficiary=token.user,
                            application=app
                        )
                        if dag.expiration_date is not None:
                            dag_expiry = strftime('%Y-%m-%dT%H:%M:%SZ', dag.expiration_date.timetuple())
                    except DataAccessGrant.DoesNotExist:
                        dag_expiry = ""
                elif app.data_access_type == "ONE_TIME":
                    expires_at = datetime.utcnow() + timedelta(seconds=body['expires_in'])
                    dag_expiry = expires_at.strftime('%Y-%m-%dT%H:%M:%SZ')
                elif app.data_access_type == "RESEARCH_STUDY":
                    dag_expiry = ""

                # Get the crosswalk for the user from token.user
                # This gets us the mbi and other info we need from the crosswalk
                if grant_type == 'refresh_token':
                    try:
                        crosswalk = Crosswalk.objects.get(user=token.user)
                        get_and_update_from_refresh(
                            crosswalk.user_mbi,
                            crosswalk.user.username,
                            crosswalk.user_hicn_hash,
                            request,
                        )
                    except Crosswalk.DoesNotExist:
                        log.debug('Unable to find crosswalk record during a token refresh')
                        return JsonResponse(
                            {'status_code': HTTPStatus.NOT_FOUND, 'message': 'Not found.'},
                            status=HTTPStatus.NOT_FOUND,
                        )
                    except UpstreamServerException:
                        log.debug('Failed to retrieve data from data source.')
                        return JsonResponse(
                            {'status_code': HTTPStatus.BAD_GATEWAY,
                             'message': 'Failed to retrieve data from data source.'},
                            status=HTTPStatus.BAD_GATEWAY,
                        )
                    except NotFound:
                        log.debug('Unable to find patient data during a token refresh')
                        return JsonResponse(
                            {'status_code': HTTPStatus.NOT_FOUND, 'message': 'Not found.'},
                            status=HTTPStatus.NOT_FOUND,
                        )

                body['access_grant_expiration'] = dag_expiry
                body = json.dumps(body)

        response = HttpResponse(content=body, status=status)
        for k, v in headers.items():
            response[k] = v
        return response


@method_decorator(csrf_exempt, name="dispatch")
class RevokeTokenView(DotRevokeTokenView):

    @method_decorator(sensitive_post_parameters("password"))
    def post(self, request, *args, **kwargs):
        try:
            validate_app_is_active(request)
        except InvalidClientError as error:
            return json_response_from_oauth2_error(error)

        return super().post(request, args, kwargs)


@method_decorator(csrf_exempt, name="dispatch")
class RevokeView(DotRevokeTokenView):

    @method_decorator(sensitive_post_parameters("password"))
    def post(self, request, *args, **kwargs):
        at_model = get_access_token_model()
        try:
            app = validate_app_is_active(request)
        except (InvalidClientError, InvalidGrantError) as error:
            return json_response_from_oauth2_error(error)

        tkn = request.POST.get('token')
        if tkn is not None:
            escaped_tkn = html.escape(tkn)
        else:
            escaped_tkn = ""

        try:
            token = at_model.objects.get(token=tkn)
        except at_model.DoesNotExist:
            log.debug(f"Token {escaped_tkn} was not found.")

        try:
            dag = DataAccessGrant.objects.get(
                beneficiary=token.user,
                application=app
            )
            dag.delete()
        except Exception:
            log.debug(f"DAG lookup failed for token {escaped_tkn}.")

        return super().post(request, args, kwargs)


@method_decorator(csrf_exempt, name="dispatch")
class IntrospectTokenView(DotIntrospectTokenView):

    def get(self, request, *args, **kwargs):
        try:
            validate_app_is_active(request)
        except InvalidClientError as error:
            return json_response_from_oauth2_error(error)

        return super(IntrospectTokenView, self).get(request, args, kwargs)

    def post(self, request, *args, **kwargs):
        try:
            validate_app_is_active(request)
        except InvalidClientError as error:
            return json_response_from_oauth2_error(error)

        return super(IntrospectTokenView, self).post(request, args, kwargs)
